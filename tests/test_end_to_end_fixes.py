# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
End-to-end & integration verification tests covering core pipeline fixes:
  - Python -> Go Synapse fluid payload routing with custom sensor_id != camera_id
  - Per-camera isolated Tracker and ModelGearbox via PipelineSupervisor
  - SliceScheduler per-gear batching, VRAM ceiling clamping, confidence filtering, real dt speed
  - Linear 2D Kalman tracker convergence and occlusion prediction
  - ASCAnalyzer waiting for real frames without noise synthesis
  - SQLite CameraNode + TrafficProfileNode persistence & IPC homography/params commands
  - VisionStateReconciler alignment with StateManager & config.SYNAPSE_UDS_PATH
  - HardwareTelemetry vram_total, delta network metrics, and TelemetryBroadcaster synapse_ports
"""

import asyncio
import json
import socket
import subprocess
from unittest.mock import MagicMock, AsyncMock, patch

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.hardware_telemetry import HardwareTelemetry
from src.common.config import config
from src.common.database import Base, SQLiteStateRepository, TrafficProfileNode
from src.common.state_manager import StateManager
from src.engine.fluid_flow_estimator import FluidFlowEstimator
from src.engine.pipeline_orchestrator import CentralPipelineOrchestrator
from src.engine.pipeline_supervisor import PipelineSupervisor
from src.engine.slice_scheduler import SliceScheduler
from src.engine.synapse_emitter import SynapseEmitter
from src.engine.triton_int8_engine import TritonInt8Engine
from src.fenix.state_reconciler import VisionStateReconciler
from src.ipc.command_handlers import CameraCommandHandler
from src.ipc.ipc_protocol import IpcMessage
from src.ipc.stdio_daemon import StdioDaemon
from src.ipc.telemetry_broadcaster import TelemetryBroadcaster
from src.network.micro_batcher import FireForgetBatcher
from src.network.synapse_builder import SynapseBuilder
from src.network.synapse_uds_client import SynapseUDSClient
from src.vision.asc_analyzer import AutonomicSceneConvergence
from src.vision.kalman_tracker import create_tracker
from src.vision.lane_mapper import AutoLaneMapper


@pytest.mark.asyncio
async def test_fluid_synapse_e2e_routing_with_distinct_sensor_id(tmp_path):
    """
    Validates that SynapseEmitter + SynapseBuilder.dispatch route by cam_id even
    when sensor_id != cam_id, and deliver fluid channels[] payloads via Go Dispatcher.
    """
    uds_path = str(tmp_path / "synapse_fluid_e2e.sock")

    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind(("127.0.0.1", 0))
    synapse_port = tcp_server.getsockname()[1]
    tcp_server.listen(1)
    tcp_server.setblocking(False)

    go_proc = subprocess.Popen(
        [
            "./bin/synapse-dispatcher",
            "-uds", uds_path,
            "-host", "127.0.0.1",
            "-base-port", str(synapse_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    synapse_conn = None
    client = SynapseUDSClient(socket_path=uds_path)
    try:
        with patch("src.network.synapse_uds_client.synapse_uds_client", client):
            await client.start()
            for _ in range(30):
                if client._writer is not None:
                    break
                await asyncio.sleep(0.1)
            assert client._writer is not None

            await client.attach_camera(
                camera_id="cam_internal_01",
                sensor_id="SP_CORREDOR_99",
                preferred_port=synapse_port,
            )

            for _ in range(30):
                try:
                    synapse_conn, _ = tcp_server.accept()
                    break
                except BlockingIOError:
                    await asyncio.sleep(0.1)
            assert synapse_conn is not None

            sm = StateManager()
            sm.upsert_camera({"id": "cam_internal_01", "name": "Corredor", "sensor_id": "SP_CORREDOR_99"})
            sm.set_camera_lifecycle("cam_internal_01", "PRODUCTION")
            sm.set_homography("cam_internal_01", [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 1.0]])

            batcher = FireForgetBatcher()
            batcher.record_fluid_sample("cam_internal_01", "ch_0", direction_deg=90.0, speed_kmh=42.5, density=0.32)

            mock_hw = MagicMock()
            mock_hw.sample_hardware.return_value = {"cpu_usage": 10, "ram_usage": 20, "vram_usage": 500, "temperature": 45}
            mock_gearbox = MagicMock()
            mock_gearbox.current_gear = "Small"

            emitter = SynapseEmitter(
                "cam_internal_01",
                batcher=batcher,
                synapse=SynapseBuilder(),
                hw_telemetry=mock_hw,
                state_mgr=sm,
                gearbox=mock_gearbox,
            )

            payload = await emitter.emit(detections=[{"bbox": [0, 0, 10, 10]}], avg_fps=12, frame_count=20)
            assert payload is not None
            assert payload["camera_id"] == "SP_CORREDOR_99"
            assert payload["calibrated"] is True

            # Allow asyncio.create_task(dispatch) to execute
            await asyncio.sleep(0.15)
            synapse_conn.settimeout(2.0)
            received = json.loads(synapse_conn.recv(4096).decode("utf-8").strip())

            assert received["camera_id"] == "SP_CORREDOR_99"
            assert received["calibrated"] is True
            assert len(received["channels"]) == 1
            assert received["channels"][0]["speed"] == 42.5
            assert received["channels"][0]["direction_deg"] == 90.0

            await client.stop()
    finally:
        if synapse_conn:
            synapse_conn.close()
        tcp_server.close()
        go_proc.terminate()
        try:
            go_proc.wait(timeout=2.0)
        except Exception:
            go_proc.kill()


def test_pipeline_supervisor_isolates_tracker_and_gearbox_per_camera():
    """Ensures each CameraAgent created by PipelineSupervisor has its own tracker and gearbox."""
    supervisor = PipelineSupervisor(state_mgr=StateManager())
    agent_a = supervisor.create_agent("cam_alpha")
    agent_b = supervisor.create_agent("cam_beta")

    assert agent_a._gearbox is not None
    assert agent_b._gearbox is not None
    assert agent_a._gearbox is not agent_b._gearbox

    assert agent_a._fluid_estimator._tracker is not agent_b._fluid_estimator._tracker

    # Mutate camera A tracker and confirm camera B stays clean
    agent_a._fluid_estimator._tracker.initialize_track("trk_a", [10, 10, 20, 20], "car")
    assert agent_a._fluid_estimator._tracker.get_track("trk_a") is not None
    assert agent_b._fluid_estimator._tracker.get_track("trk_a") is None
    supervisor.stop()


@pytest.mark.asyncio
async def test_slice_scheduler_gear_grouping_ceiling_and_conf_filtering():
    """
    Verifies SliceScheduler requests per-camera gears clamped by governor ceiling,
    batches same-gear crops, filters detections per camera confidence_threshold,
    and updates CameraAgent frame shape + dt.
    """
    sm = StateManager()
    sm.set_camera_params("cam_strict", {"confidence_threshold": 0.8})
    sm.set_camera_params("cam_lenient", {"confidence_threshold": 0.3})

    frame_720 = np.zeros((540, 960, 3), dtype=np.uint8)
    agent1 = MagicMock()
    agent1.cam_id = "cam_strict"
    agent1.active_gear = "Heavy"
    agent1.grab_and_extract_rois = AsyncMock(return_value=(frame_720, [{"rect": [10, 20, 100, 100], "has_motion": True}], "cam_strict"))

    agent2 = MagicMock()
    agent2.cam_id = "cam_lenient"
    agent2.active_gear = "Nano"
    agent2.grab_and_extract_rois = AsyncMock(return_value=(frame_720, [{"rect": [5, 5, 80, 80], "has_motion": True}], "cam_lenient"))

    mock_engine = MagicMock()
    mock_engine.infer_batch.return_value = [
        [
            {"class": "car", "confidence": 0.55, "bbox": [1, 2, 20, 20]},
            {"class": "bus", "confidence": 0.91, "bbox": [5, 6, 30, 30]},
        ]
    ]

    with patch("src.engine.slice_scheduler.state_manager", sm):
        scheduler = SliceScheduler(engine=mock_engine)
        scheduler.register_camera("cam_strict", agent1)
        scheduler.register_camera("cam_lenient", agent2)

        # Ceiling "Small" clamps "Heavy" -> "Small", keeps "Nano" -> "Nano"
        await scheduler._process_slice(["cam_strict", "cam_lenient"], gear_ceiling="Small")

    called_gears = [call.kwargs["gear"] for call in mock_engine.infer_batch.call_args_list]
    assert set(called_gears) == {"Small", "Nano"}

    # Strict camera (0.8) only keeps the 0.91 bus; offset applied
    dets_strict = agent1.post_inference_process.call_args.args[0]
    assert len(dets_strict) == 1
    assert dets_strict[0]["class"] == "bus"
    assert dets_strict[0]["bbox"] == [15, 26, 30, 30]
    assert agent1.post_inference_process.call_args.kwargs["gear_ceiling"] == "Small"

    # Lenient camera (0.3) keeps both
    dets_lenient = agent2.post_inference_process.call_args.args[0]
    assert len(dets_lenient) == 2


def test_kalman_tracker_multi_frame_and_occlusion_prediction():
    """Verifies real 2D Kalman smoothing on hits >= 3 and missed-frame advance on confirmed tracks."""
    tracker = create_tracker()
    tid = None
    for step in range(4):
        x = 100.0 + step * 10.0
        y = 200.0 + step * 4.0
        res = tracker.associate_detections([{"bbox": [x, y, 40.0, 30.0], "confidence": 0.9, "class": "car"}])
        tid = res[0]["track_id"]

    trk = tracker.get_track(tid)
    assert trk is not None
    assert trk.confirmed is True
    assert 8.0 <= trk.velocity[0] <= 12.0
    assert 2.5 <= trk.velocity[1] <= 5.5

    # One missed detection tick should advance confirmed track via Kalman velocity
    prev_x = trk.bbox[0]
    res_empty = tracker.associate_detections([])
    assert res_empty == []
    assert trk.bbox[0] > prev_x
    assert trk.time_since_update == 1


def test_fluid_flow_estimator_uses_real_dt_with_homography(tmp_path):
    """Validates metric speed computation using real delta-t instead of assuming 30 FPS."""
    sm = StateManager()
    # 10 px = 1 meter
    sm.set_homography("cam_h", [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 1.0]])

    batcher = FireForgetBatcher()
    mapper = AutoLaneMapper(topology_dir=str(tmp_path))
    with patch("src.vision.lane_mapper.state_manager", sm):
        estimator = FluidFlowEstimator("cam_h", lane_mapper=mapper, batcher=batcher, state_mgr=sm)
        # 10 px displacement in dt = 0.1s (10 FPS) -> 1.0m / 0.1s = 10 m/s = 36.0 km/h
        res = estimator.process(
            [{"bbox": [100, 100, 50, 40], "velocity": [10.0, 0.0]}],
            frame_shape=(720, 1280),
            has_motion=True,
            dt_seconds=0.1,
        )

    assert len(res) == 1
    assert res[0]["speed"] == 36.0
    assert res[0]["calibrated"] is True


def test_lane_mapper_homography_from_points_and_topology_persistence(tmp_path):
    """Validates 4-point homography estimation and JSON topology persistence."""
    img_pts = [[100.0, 400.0], [500.0, 400.0], [500.0, 200.0], [100.0, 200.0]]
    world_pts = [[0.0, 0.0], [40.0, 0.0], [40.0, 20.0], [0.0, 20.0]]
    H = AutoLaneMapper.compute_homography_from_points(img_pts, world_pts)
    assert H is not None
    assert len(H) == 3 and len(H[0]) == 3

    # Collinear/insufficient points rejected
    assert AutoLaneMapper.compute_homography_from_points(img_pts[:3], world_pts[:3]) is None

    mapper = AutoLaneMapper(topology_dir=str(tmp_path))
    assert mapper.save_topology("cam_topo", [[0, 0], [10, 10]], ["approach_n"], [90.0]) is True
    assert mapper.has_topology("cam_topo") is True
    mapper._topologies.clear()
    assert mapper.load_topology("cam_topo") is True
    assert "cam_topo" in mapper._topologies


@pytest.mark.asyncio
async def test_asc_analyzer_waits_for_real_frames_and_aborts_when_camera_removed():
    """Ensures ASCAnalyzer never synthesizes random frames when decoder returns None."""
    sm = StateManager()
    sm.upsert_camera({"id": "cam_asc", "name": "ASC Test", "address": "rtsp://test"})

    asc = AutonomicSceneConvergence()
    mock_decoder = MagicMock()
    mock_decoder.read_latest_frame.return_value = None

    with patch("src.vision.asc_analyzer.state_manager", sm), \
         patch("src.vision.stream_decoder.stream_decoder", mock_decoder), \
         patch("asyncio.sleep", new=AsyncMock()):
        ok = await asc._run_scs_calibration("cam_asc", max_empty_polls=3)

    assert ok is False
    assert "cam_asc" not in asc.calibrating_cameras

    # Now supply real static frames -> converges and promotes to PRODUCTION
    static_frame = np.full((120, 160, 3), 120, dtype=np.uint8)
    mock_decoder.read_latest_frame.return_value = static_frame
    with patch("src.vision.asc_analyzer.state_manager", sm), \
         patch("src.vision.stream_decoder.stream_decoder", mock_decoder), \
         patch("asyncio.sleep", new=AsyncMock()):
        await asc.start_calibration("cam_asc")

    assert sm.is_camera_production("cam_asc") is True
    assert sm.get_cameras()[0]["scs"] >= 90.0


def test_sqlite_persistence_and_ipc_homography_handlers(tmp_path):
    """Validates end-to-end SQLite persistence + reload and IPC homography/params handlers."""
    db_file = tmp_path / "test_svision.db"
    mem_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=mem_engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=mem_engine)
    repo = SQLiteStateRepository(session_factory=Session)

    sm = StateManager()
    sm.attach_persistence(repo, load_existing=False)

    events = []
    with patch("src.ipc.command_handlers.state_manager", sm), \
         patch("src.common.state_manager.state_manager", sm):
        handler = CameraCommandHandler(event_emitter=lambda ev, data: events.append((ev, data)), loop_getter=lambda: None)

        res_add = {}
        handler.handle_add_camera(
            IpcMessage(action="add_camera", payload={"id": "cam_db_1", "name": "DB Cam", "address": "rtsp://cam/1", "sensor_id": "S1", "synapse_port": 9020}),
            lambda ok, result=None, error=None: res_add.update({"ok": ok, "result": result, "error": error}),
        )
        assert res_add["ok"] is True

        res_h = {}
        handler.handle_set_homography(
            IpcMessage(
                action="set_homography",
                payload={
                    "camera_id": "cam_db_1",
                    "image_points": [[0, 0], [100, 0], [100, 100], [0, 100]],
                    "world_points": [[0, 0], [10, 0], [10, 10], [0, 10]],
                },
            ),
            lambda ok, result=None, error=None: res_h.update({"ok": ok, "result": result, "error": error}),
        )
        assert res_h["ok"] is True
        assert res_h["result"]["calibrated"] is True

        res_p = {}
        handler.handle_update_camera_params(
            IpcMessage(action="update_camera_params", payload={"camera_id": "cam_db_1", "params": {"confidence_threshold": 0.6, "approach": "north"}}),
            lambda ok, result=None, error=None: res_p.update({"ok": ok, "result": result, "error": error}),
        )
        assert res_p["ok"] is True
        assert res_p["result"]["params"]["confidence_threshold"] == 0.6

    sm.record_traffic_sample("cam_db_1", 0.45, 51.2, min_interval_s=0.0)

    # Rehydrate into a clean StateManager instance
    sm_reloaded = StateManager()
    loaded_cams = sm_reloaded.attach_persistence(repo, load_existing=True)
    assert len(loaded_cams) == 1
    assert loaded_cams[0]["id"] == "cam_db_1"
    assert loaded_cams[0]["calibrated"] is True
    assert sm_reloaded.get_homography("cam_db_1") is not None
    assert sm_reloaded.get_camera_params("cam_db_1")["confidence_threshold"] == 0.6

    with Session() as sess:
        profiles = sess.query(TrafficProfileNode).filter_by(camera_id="cam_db_1").all()
        assert len(profiles) == 1
        assert profiles[0].average_velocity == 51.2


def test_reconciler_uses_config_socket_and_real_state_manager():
    """Verifies VisionStateReconciler uses config.SYNAPSE_UDS_PATH and real StateManager.get_cameras()."""
    sm = StateManager()
    sm.upsert_camera({"id": "cam_rec_1", "name": "Reconcile Cam", "address": "rtsp://x"})

    reconciler = VisionStateReconciler(state_mgr=sm)
    assert reconciler._uds_socket_path == config.SYNAPSE_UDS_PATH
    assert reconciler.reconcile_state() is True
    summary = reconciler.get_status_summary()
    assert summary["reconciled_cameras"] == ["cam_rec_1"]


def test_hardware_telemetry_first_tick_and_broadcaster_synapse_ports():
    """Verifies no false bandwidth spike on tick 1 and TelemetryBroadcaster emits synapse_ports."""
    hw = HardwareTelemetry()
    first = hw.sample_network(1, 2, dropped_frames=0, frames_received=100)
    assert first["bandwidth_peak"] == 0.0
    assert first["packet_delivery"] == "100.00"

    second = hw.sample_network(1, 2, dropped_frames=1, frames_received=109)
    assert float(second["packet_delivery"]) == 90.0

    sample = hw.sample_hardware()
    assert "vram_total" in sample


@pytest.mark.asyncio
async def test_telemetry_broadcaster_emits_synapse_ports_topic():
    """Verifies TelemetryBroadcaster loop emits synapse_ports alongside core topics."""
    emitted = []
    broadcaster = TelemetryBroadcaster(event_emitter=lambda topic, data: emitted.append((topic, data)), interval=0.01)

    async def stop_soon():
        await asyncio.sleep(0.03)
        broadcaster.stop()

    await asyncio.gather(broadcaster.run_loop(), stop_soon())
    topics = {t for t, _ in emitted}
    assert {"engine_stats", "network_stats", "cameras", "synapse_ports", "network_latency"}.issubset(topics)


def test_triton_engine_and_stdio_daemon_lifecycle(tmp_path):
    """Covers TritonInt8Engine lazy load fallback/eviction, Orchestrator base warmup, and StdioDaemon shutdown."""
    engine = TritonInt8Engine(models_dir=str(tmp_path))
    assert engine.get_model("UnknownTier") is None
    assert engine.get_model("Nano") is None
    assert engine.infer_batch([], gear="Nano") == []
    assert engine.infer_batch([np.zeros((32, 32, 3), dtype=np.uint8)], gear="Nano") == [[]]

    # Mock model path and test idle eviction
    fake_pt = tmp_path / "yolo11s.pt"
    fake_pt.write_bytes(b"mock")
    mock_box = MagicMock()
    mock_box.conf = [0.92]
    mock_box.cls = [0]
    mock_box.xyxy = [MagicMock(tolist=lambda: [1.0, 2.0, 21.0, 22.0])]
    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_yolo = MagicMock(return_value=[mock_result])
    mock_yolo.names = {0: "car"}

    with patch("ultralytics.YOLO", return_value=mock_yolo):
        out = engine.infer_batch([np.zeros((40, 40, 3), dtype=np.uint8)], gear="Small", conf_threshold=0.5)
    assert len(out) == 1 and out[0][0]["class"] == "car"

    engine._last_access["Small"] = 0.0
    engine.evict_idle_models(dwell_seconds=1.0)
    assert "Small" not in engine._loaded_models

    # Orchestrator init + shutdown + StdioDaemon clean shutdown
    daemon = StdioDaemon(on_shutdown=lambda: None)
    daemon.shutdown()
    assert daemon._is_shutting_down is True

    orch = CentralPipelineOrchestrator(slice_scheduler=SliceScheduler(engine=engine))
    assert orch.supervisor is not None


def test_triton_engine_batch_chunking_and_metadata(tmp_path):
    """Validates TensorRT engine batch metadata parsing and safe chunking above max_batch."""
    meta_bytes = json.dumps({"batch": 4}).encode("utf-8")
    fake_engine = tmp_path / "yolo11n.engine"
    fake_engine.write_bytes(len(meta_bytes).to_bytes(4, "little") + meta_bytes + b"\x00" * 16)

    engine = TritonInt8Engine(models_dir=str(tmp_path))
    call_sizes = []

    def fake_forward(chunk, verbose=False, half=False):
        call_sizes.append(len(chunk))
        res = []
        for idx in range(len(chunk)):
            box = MagicMock()
            box.conf = [0.9]
            box.cls = [0]
            box.xyxy = [MagicMock(tolist=lambda i=idx: [float(i), 2.0, float(i + 10), 12.0])]
            r = MagicMock()
            r.boxes = [box]
            res.append(r)
        return res

    mock_yolo = MagicMock(side_effect=fake_forward)
    mock_yolo.names = {0: "car"}

    with patch("ultralytics.YOLO", return_value=mock_yolo):
        crops = [np.zeros((32, 32, 3), dtype=np.uint8) for _ in range(10)]
        outputs = engine.infer_batch(crops, gear="Nano", conf_threshold=0.5)

    assert call_sizes == [4, 4, 2]
    assert len(outputs) == 10
    assert all(len(dets) == 1 and dets[0]["class"] == "car" for dets in outputs)
