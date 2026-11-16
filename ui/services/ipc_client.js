/*
 * SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
 * Copyright (C) 2026 Noxfort Systems
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * SPDX-FileCopyrightText: 2026 Noxfort Systems
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * File: ipc_client.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * IPC Telemetry Client — Tauri v2 Native Bridge (Standard I/O Zero-Port Architecture).
 *
 * Single source of truth for all backend data flowing into the React layer.
 * Receives domain events via Tauri's native event pub/sub system and sends
 * commands via Tauri commands directly to the child Python daemon.
 */

import { generateDefaultCameraParams } from '../constants/cameraConfig';

class IPCClient {
    constructor() {
        /** @type {Map<string, Set<Function>>} */
        this._subscribers = new Map();
        this._lastDataTs = 0;
        this._active = false;
        this._backendError = null;
        this._camerasContext = [];
        this._synapseHost = '127.0.0.1';
        this._synapsePorts = {};
        this._unlisteners = [];
        this._isDemo = false;
        this._simTimer = null;
        this._simTick = 0;

        this._boot();
    }

    // ── Bootstrap ──────────────────────────────────────────────────

    async _boot() {
        const isBrowser = typeof window !== 'undefined';
        const isDemo = isBrowser && (
            window.location.search.includes('demo=true') ||
            !window.__TAURI_INTERNALS__
        );
        const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';

        if (isDemo && !isTest) {
            this._startMockSimulation();
            return;
        }

        try {
            const { listen } = await import('@tauri-apps/api/event');
            const { invoke } = await import('@tauri-apps/api/core');

            const topics = [
                'engine_stats',
                'network_stats',
                'cameras',
                'synapse_ports',
                'network_latency',
                'gpu_health_alert',
                'ready',
            ];

            // Subscribe to each domain event emitted from Rust
            for (const topic of topics) {
                const unlisten = await listen(`svision:${topic}`, (event) => {
                    this._lastDataTs = Date.now();
                    const wasActive = this._active;
                    this._active = true;

                    if (!wasActive) {
                        this._dispatch('connection_status', 'online');
                    }

                    if (topic === 'cameras' && Array.isArray(event.payload)) {
                        this._camerasContext = event.payload;
                    }
                    if (topic === 'synapse_ports' && event.payload && typeof event.payload === 'object') {
                        this._synapsePorts = event.payload;
                    }

                    this._dispatch(topic, event.payload);
                });
                this._unlisteners.push(unlisten);
            }

            // Listen for backend error events
            const unlistenErr = await listen('svision:backend_error', (event) => {
                console.error('[SVision IPC] ❌ Backend process error:', event.payload);
                this._backendError = event.payload;
                this._dispatch('backend_error', event.payload);
            });
            this._unlisteners.push(unlistenErr);

            // Listen for command responses
            const unlistenResp = await listen('svision:response', (event) => {
                const resp = event.payload;
                if (resp?.id === 'init-sync' && resp.success && resp.result) {
                    const res = resp.result;
                    if (res.cameras) {
                        this._camerasContext = res.cameras;
                        this._dispatch('cameras', res.cameras);
                    }
                    if (res.engine_stats) {
                        this._dispatch('engine_stats', res.engine_stats);
                    }
                    if (res.network_stats) {
                        this._dispatch('network_stats', res.network_stats);
                    }
                    if (res.synapse_ports) {
                        this._synapsePorts = res.synapse_ports;
                        this._dispatch('synapse_ports', res.synapse_ports);
                    }
                    if (res.synapse_host) {
                        this._synapseHost = res.synapse_host;
                        this._dispatch('synapse_host', res.synapse_host);
                    }
                }
            });
            this._unlisteners.push(unlistenResp);

            // Check initial backend status
            try {
                const statusInfo = await invoke('get_backend_status');
                if (statusInfo && statusInfo.status === 'failed' && statusInfo.error) {
                    this._backendError = { error: statusInfo.error, code: 'BOOT_FAILED' };
                    this._dispatch('backend_error', this._backendError);
                }
            } catch (statusErr) {
                console.debug('[SVision IPC] Could not query backend status:', statusErr);
            }

            // Request initial state synchronization
            try {
                await invoke('send_svision_command', {
                    action: 'sync_state',
                    payload: {},
                    id: 'init-sync',
                });
            } catch (err) {
                console.debug('[SVision IPC] Initial sync requested before backend ready:', err);
            }

            // Watchdog: detect offline status if no event received within 5s
            setInterval(() => {
                const wasActive = this._active;
                this._active = Date.now() - this._lastDataTs < 5000;
                if (wasActive !== this._active) {
                    this._dispatch('connection_status', this._active ? 'online' : 'offline');
                }
            }, 2000);

            console.log('[SVision IPC] Tauri v2 IPC bridge connected successfully.');
        } catch (err) {
            console.warn('[SVision IPC] Running outside Tauri runtime:', err);
            const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';
            if (!isTest) {
                this._startMockSimulation();
            }
        }
    }

    // ── Mock Demonstration Simulation ──────────────────────────────

    _startMockSimulation() {
        if (this._isDemo && this._simTimer) return;
        this._isDemo = true;
        this._dispatch('demo_mode', true);
        this._active = true;
        this._lastDataTs = Date.now();
        console.info('🎭 [SVision IPC] Inicializado em modo demonstração (Mock Telemetry).');

        const defaultCameras = [
            {
                id: 'cam_paulista_01',
                name: 'Av. Paulista / Al. Campinas',
                address: 'rtsp://edge-paulista.internal/stream1',
                sensor_id: 'SP_PAULISTA_01',
                synapse_port: 9001,
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 99.4,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 14250, dropped: 0 },
                synapse: {
                    sensor_id: 'SP_PAULISTA_01',
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 32, speed_kmh: 46.5, occupancy: 0.38, density: 16.2 },
                        approach_2: { count: 24, speed_kmh: 51.0, occupancy: 0.26, density: 11.4 },
                        approach_3: { count: 41, speed_kmh: 38.2, occupancy: 0.49, density: 24.1 },
                        approach_4: { count: 18, speed_kmh: 48.0, occupancy: 0.18, density: 8.5 }
                    }
                },
                parameters: generateDefaultCameraParams()
            },
            {
                id: 'cam_consolacao_02',
                name: 'Rua da Consolação / Rebouças',
                address: 'rtsp://edge-consolacao.internal/stream1',
                sensor_id: 'SP_CONSOLACAO_02',
                synapse_port: 9002,
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 98.7,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 13980, dropped: 0 },
                synapse: {
                    sensor_id: 'SP_CONSOLACAO_02',
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 27, speed_kmh: 42.0, occupancy: 0.35, density: 14.8 },
                        approach_2: { count: 35, speed_kmh: 39.5, occupancy: 0.44, density: 19.2 },
                        approach_3: { count: 19, speed_kmh: 49.0, occupancy: 0.21, density: 9.3 },
                        approach_4: { count: 15, speed_kmh: 47.8, occupancy: 0.16, density: 7.2 }
                    }
                },
                parameters: generateDefaultCameraParams()
            },
            {
                id: 'cam_pinheiros_03',
                name: 'Marginal Pinheiros / Pte. Estaiada',
                address: 'rtsp://edge-pinheiros.internal/stream1',
                sensor_id: 'SP_PINHEIROS_03',
                synapse_port: 9003,
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 99.1,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 14610, dropped: 0 },
                synapse: {
                    sensor_id: 'SP_PINHEIROS_03',
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 54, speed_kmh: 68.4, occupancy: 0.42, density: 26.5 },
                        approach_2: { count: 48, speed_kmh: 71.0, occupancy: 0.39, density: 23.8 },
                        approach_3: { count: 39, speed_kmh: 65.2, occupancy: 0.31, density: 18.4 },
                        approach_4: { count: 22, speed_kmh: 70.1, occupancy: 0.20, density: 10.9 }
                    }
                },
                parameters: generateDefaultCameraParams()
            },
            {
                id: 'cam_radial_04',
                name: 'Radial Leste / Metrô Tatuapé',
                address: 'rtsp://edge-radial.internal/stream1',
                sensor_id: 'SP_RADIAL_04',
                synapse_port: 9004,
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 97.9,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 13540, dropped: 0 },
                synapse: {
                    sensor_id: 'SP_RADIAL_04',
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 45, speed_kmh: 54.0, occupancy: 0.40, density: 22.1 },
                        approach_2: { count: 38, speed_kmh: 58.2, occupancy: 0.36, density: 18.7 },
                        approach_3: { count: 29, speed_kmh: 52.1, occupancy: 0.28, density: 13.9 },
                        approach_4: { count: 25, speed_kmh: 55.4, occupancy: 0.24, density: 11.8 }
                    }
                },
                parameters: generateDefaultCameraParams()
            }
        ];

        this._camerasContext = defaultCameras;

        setTimeout(() => {
            this._dispatch('connection_status', 'online');
            this._dispatch('cameras', this._camerasContext);

            const now = Date.now();
            for (let i = 20; i >= 0; i--) {
                this._dispatch('network_latency', {
                    latency_ms: parseFloat((1.6 + Math.sin(i * 0.4) * 0.4).toFixed(2)),
                    timestamp: now - i * 1000
                });
            }

            this._emitMockTick();
        }, 100);

        this._simTimer = setInterval(() => {
            this._simTick++;
            this._emitMockTick();
        }, 1000);
    }

    _emitMockTick() {
        const tick = this._simTick;
        this._lastDataTs = Date.now();

        const cpu = parseFloat((24 + Math.sin(tick * 0.4) * 3.2).toFixed(1));
        const ram = parseFloat((38 + Math.cos(tick * 0.3) * 1.5).toFixed(1));
        const vram = parseFloat((4200 + Math.sin(tick * 0.2) * 150).toFixed(0));
        const temp = parseFloat((56 + Math.sin(tick * 0.3) * 1.4).toFixed(1));
        const fps = parseFloat((119.2 + Math.cos(tick * 0.5) * 1.8).toFixed(1));

        this._dispatch('engine_stats', {
            cpu_usage: cpu,
            ram_usage: ram,
            vram_usage: vram,
            vram_trend: { value: "+1.2%", isPositive: true },
            temperature: temp,
            temp_trend: { value: "-0.4°C", isPositive: true },
            fps_average: fps,
            fps_trend: { value: "+1.5 FPS", isPositive: true },
            dropped_frames: 0,
            drops_trend: { value: "0%", isPositive: true },
            active_gear: 'TensorRT INT8',
            recent_operations: [
                { id: 'OP-TRT-8921', name: 'Heuristic Check', status: 'Completed' },
                { id: 'OP-TRT-8920', name: 'TensorRT INT8 Batch', status: 'Completed' },
                { id: 'OP-TRT-8919', name: 'NVDEC Multi-Decode', status: 'Completed' },
                { id: 'OP-TRT-8918', name: 'Spatial-Temporal Tracker', status: 'Completed' },
                { id: 'OP-TRT-8917', name: 'Synapse UDS Packet Batcher', status: 'Completed' }
            ]
        });

        this._dispatch('network_stats', {
            active_connections: this._camerasContext.length,
            conn_trend: "+1",
            packet_delivery: "99.98",
            delivery_trend: "Optimal",
            bandwidth_peak: parseFloat((42.5 + Math.sin(tick * 0.2) * 2.5).toFixed(1)),
            bandwidth_trend: "+2.4 MB/s"
        });

        const lat = parseFloat((1.65 + Math.sin(tick * 0.5) * 0.35).toFixed(2));
        this._dispatch('network_latency', {
            latency_ms: lat,
            timestamp: Date.now()
        });

        this._camerasContext.forEach((cam, idx) => {
            if (cam.stream_health) {
                cam.stream_health.frames_received += 30;
            }
            if (cam.synapse && cam.synapse.traffic) {
                const t = cam.synapse.traffic;
                for (const key of Object.keys(t)) {
                    const base = (idx + 1) * 8 + 10;
                    t[key].count = Math.max(5, Math.floor(base + Math.sin(tick + idx) * 7));
                    t[key].speed_kmh = parseFloat((44 + Math.cos(tick + idx) * 5).toFixed(1));
                    t[key].occupancy = parseFloat((0.25 + Math.sin(tick * 0.3 + idx) * 0.08).toFixed(2));
                    t[key].density = parseFloat((12 + Math.sin(tick * 0.4 + idx) * 3).toFixed(1));
                }
            }
        });

        this._dispatch('cameras', [...this._camerasContext]);
    }

    // ── Pub/Sub ────────────────────────────────────────────────────

    subscribe(topic, callback) {
        if (!this._subscribers.has(topic)) {
            this._subscribers.set(topic, new Set());
        }
        this._subscribers.get(topic).add(callback);

        // Immediate callback with cached camerasContext if subscribing to cameras
        if (topic === 'cameras' && this._camerasContext.length > 0) {
            try {
                callback(this._camerasContext);
            } catch (e) {
                console.error('[SVision IPC] Initial camera subscriber error:', e);
            }
        }

        // Immediate callback with cached backendError if subscribing to backend_error
        if (topic === 'backend_error' && this._backendError) {
            try {
                callback(this._backendError);
            } catch (e) {
                console.error('[SVision IPC] Initial backend_error subscriber error:', e);
            }
        }

        if (topic === 'synapse_host' && this._synapseHost) {
            try {
                callback(this._synapseHost);
            } catch (e) {
                console.error('[SVision IPC] Initial synapse_host subscriber error:', e);
            }
        }

        if (topic === 'synapse_ports' && Object.keys(this._synapsePorts).length > 0) {
            try {
                callback(this._synapsePorts);
            } catch (e) {
                console.error('[SVision IPC] Initial synapse_ports subscriber error:', e);
            }
        }

        // Return unsubscribe function for React cleanup
        return () => {
            const subs = this._subscribers.get(topic);
            if (subs) subs.delete(callback);
        };
    }

    _dispatch(topic, data) {
        const subs = this._subscribers.get(topic);
        if (subs) {
            subs.forEach((cb) => {
                try {
                    cb(data);
                } catch (e) {
                    console.error(`[SVision IPC] Error in subscriber for ${topic}:`, e);
                }
            });
        }
    }

    // ── Outbound Commands (renderer → Tauri Rust → Python backend) ──

    async sendCommand(command, payload) {
        if (this._isDemo) {
            console.log(`[SVision Demo IPC] Command handled: "${command}"`, payload);
            return;
        }
        try {
            const { invoke } = await import('@tauri-apps/api/core');
            const id = Math.random().toString(36).substring(2, 9);
            await invoke('send_svision_command', {
                action: command,
                payload: payload ?? {},
                id,
            });
        } catch (err) {
            console.warn(`[SVision IPC] Cannot send "${command}":`, err);
        }
    }

    addCamera(cameraObject) {
        if (this._isDemo) {
            const nextPort = 9001 + this._camerasContext.length;
            const enrichedCam = {
                id: cameraObject.id || `manual_cam_${Date.now()}`,
                name: cameraObject.name || 'Nova Câmera Urbana',
                address: cameraObject.address || 'rtsp://edge-local.internal/stream1',
                sensor_id: cameraObject.sensor_id || `SP_CAM_${this._camerasContext.length + 1}`,
                synapse_port: cameraObject.synapse_port || nextPort,
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 99.2,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 150, dropped: 0 },
                synapse: {
                    sensor_id: cameraObject.sensor_id || `SP_CAM_${this._camerasContext.length + 1}`,
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 18, speed_kmh: 45.2, occupancy: 0.28, density: 12.4 },
                        approach_2: { count: 22, speed_kmh: 42.1, occupancy: 0.32, density: 15.0 },
                        approach_3: { count: 14, speed_kmh: 48.0, occupancy: 0.19, density: 8.7 },
                        approach_4: { count: 9, speed_kmh: 50.4, occupancy: 0.14, density: 5.9 }
                    }
                },
                parameters: generateDefaultCameraParams(),
                ...cameraObject
            };
            this._camerasContext.push(enrichedCam);
            this._dispatch('cameras', [...this._camerasContext]);
            return;
        }

        this._camerasContext.push(cameraObject);
        this._dispatch('cameras', [...this._camerasContext]);
        this.sendCommand('add_camera', cameraObject);
    }

    removeCamera(cameraId) {
        this._camerasContext = this._camerasContext.filter((c) => c.id !== cameraId);
        this._dispatch('cameras', [...this._camerasContext]);
        if (!this._isDemo) {
            this.sendCommand('remove_camera', { id: cameraId });
        }
    }

    setCameras(importedList) {
        if (this._isDemo) {
            const enrichedList = importedList.map((cam, idx) => ({
                id: cam.id || `imported_cam_${idx}_${Date.now()}`,
                name: cam.name,
                address: cam.address,
                sensor_id: cam.sensor_id || `SP_IMP_${idx + 1}`,
                synapse_port: cam.synapse_port || (9005 + idx),
                synapse_status: 'CONNECTED',
                status: 'online',
                scs: 98.9,
                fps: 30,
                active_gear: 'TensorRT INT8',
                stream_health: { is_receiving: true, frames_received: 90, dropped: 0 },
                synapse: {
                    sensor_id: cam.sensor_id || `SP_IMP_${idx + 1}`,
                    window_ms: 1000,
                    timestamp: new Date().toLocaleTimeString(),
                    traffic: {
                        approach_1: { count: 25, speed_kmh: 44.0, occupancy: 0.31, density: 13.8 },
                        approach_2: { count: 19, speed_kmh: 47.5, occupancy: 0.24, density: 10.2 },
                        approach_3: { count: 30, speed_kmh: 41.2, occupancy: 0.38, density: 17.5 },
                        approach_4: { count: 16, speed_kmh: 49.0, occupancy: 0.18, density: 7.9 }
                    }
                },
                parameters: generateDefaultCameraParams(),
                ...cam
            }));
            this._camerasContext = enrichedList;
            this._dispatch('cameras', [...this._camerasContext]);
            return;
        }

        this._camerasContext = importedList;
        this._dispatch('cameras', [...this._camerasContext]);
        this.sendCommand('set_cameras', importedList);
    }

    updateSynapseConfig(config) {
        if (config?.host) {
            this._synapseHost = String(config.host).trim();
            this._dispatch('synapse_host', this._synapseHost);
        }
        if (!this._isDemo) {
            this.sendCommand('update_synapse_config', config);
        } else {
            console.log('[SVision Demo IPC] Config Synapse atualizada:', config);
        }
    }

    setHomography(cameraId, calibrationPayload) {
        const payload = { camera_id: cameraId, ...calibrationPayload };
        if (this._isDemo) {
            this._camerasContext = this._camerasContext.map((c) =>
                c.id === cameraId ? { ...c, calibrated: true } : c
            );
            this._dispatch('cameras', [...this._camerasContext]);
            return;
        }
        this.sendCommand('set_homography', payload);
    }

    updateCameraParams(cameraId, params) {
        const payload = { camera_id: cameraId, params };
        if (this._isDemo) {
            this._camerasContext = this._camerasContext.map((c) =>
                c.id === cameraId ? { ...c, tuning_params: { ...(c.tuning_params || {}), ...params } } : c
            );
            this._dispatch('cameras', [...this._camerasContext]);
            return;
        }
        this.sendCommand('update_camera_params', payload);
    }

    // ── Status ─────────────────────────────────────────────────────

    get isActive() {
        return this._active;
    }

    get isDemo() {
        return this._isDemo;
    }

    get synapseHost() {
        return this._synapseHost;
    }

    get backendError() {
        return this._backendError;
    }

    get camerasContext() {
        return this._camerasContext;
    }
}

export const ipcClient = new IPCClient();
