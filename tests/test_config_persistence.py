# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# File: test_config_persistence.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Unit tests for configuration persistence, INI synchronization, and runtime overrides.
"""

import os
import tempfile
import configparser
from src.common.config import SVisionConfig
from src.ipc.command_handlers import CameraCommandHandler
from src.ipc.ipc_protocol import IpcMessage


def test_config_reads_from_ini():
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as f:
        f.write("[SYNAPSE]\nhost = 192.168.10.42\nbase_port = 9050\n")
        temp_ini = f.name

    try:
        old_env = os.environ.pop("SVISION_SYNAPSE_HOST", None)
        old_port_env = os.environ.pop("SVISION_SYNAPSE_BASE_PORT", None)
        
        cfg = SVisionConfig()
        cfg.SETTINGS_FILE = temp_ini
        cfg._load_ini_overrides()

        assert cfg.SYNAPSE_HOST == "192.168.10.42"
        assert cfg.SYNAPSE_BASE_PORT == 9050
    finally:
        if old_env:
            os.environ["SVISION_SYNAPSE_HOST"] = old_env
        if old_port_env:
            os.environ["SVISION_SYNAPSE_BASE_PORT"] = old_port_env
        if os.path.exists(temp_ini):
            os.remove(temp_ini)


def test_config_save_synapse_host():
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as f:
        f.write("[SYNAPSE]\nhost = 127.0.0.1\n")
        temp_ini = f.name

    try:
        cfg = SVisionConfig()
        cfg.SETTINGS_FILE = temp_ini
        cfg.save_synapse_host("10.0.0.99")

        assert cfg.SYNAPSE_HOST == "10.0.0.99"

        # Verify disk persistence
        parser = configparser.ConfigParser()
        parser.read(temp_ini)
        assert parser.get("SYNAPSE", "host") == "10.0.0.99"
    finally:
        if os.path.exists(temp_ini):
            os.remove(temp_ini)


def test_ipc_handler_persists_synapse_host():
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as f:
        f.write("[SYNAPSE]\nhost = 127.0.0.1\n")
        temp_ini = f.name

    try:
        from src.common.config import config
        original_ini = config.SETTINGS_FILE
        config.SETTINGS_FILE = temp_ini

        events = []
        handler = CameraCommandHandler(event_emitter=lambda topic, data: events.append((topic, data)))

        response = {}
        def mock_responder(success, result=None, error=None):
            response["success"] = success
            response["result"] = result
            response["error"] = error

        msg = IpcMessage(action="update_synapse_config", payload={"host": "172.16.0.5"})
        handler.handle_update_synapse_config(msg, mock_responder)

        assert response["success"] is True
        assert response["result"]["host"] == "172.16.0.5"
        assert config.SYNAPSE_HOST == "172.16.0.5"

        parser = configparser.ConfigParser()
        parser.read(temp_ini)
        assert parser.get("SYNAPSE", "host") == "172.16.0.5"

        # Restore original
        config.SETTINGS_FILE = original_ini
        config.save_synapse_host("127.0.0.1")
    finally:
        if os.path.exists(temp_ini):
            os.remove(temp_ini)
