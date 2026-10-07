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

# File: security.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Local Authentication and Token Manager (SOLID: SRP & DIP).

Encapsulates generation, file-based persistence with secure POSIX permissions,
and in-memory retrieval of the local API key used for frontend handshake authentication.
"""

import os
import secrets
import logging
from typing import Optional

from src.common.config import config

logger = logging.getLogger("svision.api.security")


class LocalTokenManager:
    """
    Manages generation, storage, and retrieval of the local ephemeral API token.
    """

    def __init__(self, key_file_path: Optional[str] = None):
        self._key_file = key_file_path or config.API_KEY_FILE
        self._api_key: str = ""

    @property
    def api_key(self) -> str:
        """Returns the current cached in-memory API key."""
        return self._api_key

    def get_token(self) -> str:
        """Returns the current API key, generating one if not yet initialized."""
        if not self._api_key:
            return self.generate_key()
        return self._api_key

    def generate_key(self) -> str:
        """
        Generates a cryptographically strong local API key,
        writes it to the specified file with 0o600 permissions,
        and caches it in memory.
        """
        key = secrets.token_hex(32)
        self._api_key = key
        try:
            with open(self._key_file, "w") as f:
                f.write(key)
            os.chmod(self._key_file, 0o600)
            logger.info(f"Local API key generated and written to {self._key_file}")
        except Exception as e:
            logger.error(f"Failed to write API key file to {self._key_file}: {e}")
        return key

    def clear(self) -> None:
        """Clears the cached key and optionally removes the key file."""
        self._api_key = ""
        try:
            if os.path.exists(self._key_file):
                os.unlink(self._key_file)
        except OSError as e:
            logger.warning(f"Could not delete API key file {self._key_file}: {e}")


# Global singleton instance
token_manager = LocalTokenManager()
