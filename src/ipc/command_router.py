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

# File: command_router.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
IPC Command Router and Registry.

Provides an extensible registry for IPC action handlers.
Open for extension by registering new command handlers without modifying the daemon core.
"""

from typing import Callable, Dict, Any, Optional
import inspect
import logging

from src.ipc.ipc_protocol import IpcMessage, IpcResponse

logger = logging.getLogger("svision.ipc.router")

Responder = Callable[[bool, Any, Optional[str]], None]
CommandHandler = Callable[[IpcMessage, Responder], Any]


class IpcCommandRouter:
    """
    Extensible command registry and dispatcher for IPC actions.
    """

    def __init__(self):
        self._handlers: Dict[str, CommandHandler] = {}

    def register(self, action: str, handler: CommandHandler) -> None:
        """Registers a handler for a specific action name."""
        self._handlers[action] = handler

    def unregister(self, action: str) -> None:
        """Removes a handler for an action."""
        self._handlers.pop(action, None)

    def has_action(self, action: str) -> bool:
        """Checks if an action handler is registered."""
        return action in self._handlers

    def dispatch(
        self,
        msg: IpcMessage,
        response_emitter: Callable[[IpcResponse], None],
    ) -> None:
        """
        Dispatches an incoming message to its registered action handler.
        Handles synchronous returns, explicit callback responses, and unhandled errors.
        """
        action = msg.action
        msg_id = msg.id

        if action not in self._handlers:
            logger.warning(f"[IPC Router] ⚠️ Unrecognized action: '{action}'")
            response_emitter(
                IpcResponse(id=msg_id, success=False, error=f"Unknown action: {action}")
            )
            return

        handler = self._handlers[action]

        def responder(success: bool, result: Any = None, error: Optional[str] = None) -> None:
            if not success:
                logger.error(f"[IPC Router] ❌ Failed response for '{action}' (id={msg_id}): {error}")
            response_emitter(
                IpcResponse(id=msg_id, success=success, result=result, error=error)
            )

        try:
            sig = inspect.signature(handler)
            num_params = len(sig.parameters)

            if num_params >= 2:
                res = handler(msg, responder)
            else:
                res = handler(msg)

            if res is not None:
                if isinstance(res, IpcResponse):
                    response_emitter(res)
                else:
                    responder(True, res)

        except Exception as ex:
            logger.error(f"[IPC Router] ❌ Unhandled exception executing '{action}': {ex}", exc_info=True)
            responder(False, error=f"Internal error executing '{action}': {ex}")
