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

# File: main.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Entry point for the SVision Backend.
Includes LGPD-compliant exception handling that sanitizes image data from tracebacks.
"""
import gc
import os
import sys
import logging
import traceback
import warnings
import uvicorn

# Suppress the specific pynvml deprecation warning from Torch/Direct imports
warnings.filterwarnings("ignore", category=FutureWarning, module=".*pynvml.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*pynvml.*")

# ── Logging Configuration ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-24s │ %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

# Silence overly verbose third-party loggers
for _quiet in ("watchfiles.main", "httpcore", "httpx"):
    logging.getLogger(_quiet).setLevel(logging.WARNING)

logger = logging.getLogger("svision.boot")


# ── LGPD Image Sanitization ───────────────────────────────────────────
# Prevents NumPy/Tensor image data from leaking into tracebacks and logs.
# If an unhandled exception occurs while a frame array is in scope,
# Python's default handler may serialize locals to disk.
# This hook scrubs binary vision data before logging the traceback.

def _is_sensitive_variable(value) -> bool:
    """
    Identifies variables that may contain image/video data.
    Returns True for NumPy arrays, PyTorch tensors, and large byte buffers.
    """
    try:
        import numpy as np
        if isinstance(value, np.ndarray) and value.nbytes > 1024:
            return True
    except ImportError:
        pass
    
    try:
        import torch
        if isinstance(value, torch.Tensor) and value.nelement() > 256:
            return True
    except ImportError:
        pass
    
    if isinstance(value, (bytes, bytearray)) and len(value) > 1024:
        return True
    
    return False


def _get_scrubbed_repr(value) -> str:
    """Creates a safe representation string for sensitive variables."""
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return f"<SCRUBBED: ndarray shape={value.shape} dtype={value.dtype}>"
    except ImportError:
        pass
    
    try:
        import torch
        if isinstance(value, torch.Tensor):
            return f"<SCRUBBED: Tensor shape={tuple(value.shape)} dtype={value.dtype}>"
    except ImportError:
        pass
    
    if isinstance(value, (bytes, bytearray)):
        return f"<SCRUBBED: {type(value).__name__} len={len(value)}>"
    
    return "<SCRUBBED>"


def _sanitized_excepthook(exc_type, exc_value, exc_tb):
    """
    LGPD-compliant exception handler.
    Walks the traceback frame chain, scrubs any local variables containing
    image/tensor data, then logs only the sanitized traceback string.
    """
    sanitized_logger = logging.getLogger("svision.crash")
    
    # Walk all frames and scrub sensitive locals
    scrubbed_vars = []
    tb = exc_tb
    while tb is not None:
        frame = tb.tb_frame
        locals_to_scrub = []
        
        for var_name, var_value in frame.f_locals.items():
            if _is_sensitive_variable(var_value):
                scrubbed_repr = _get_scrubbed_repr(var_value)
                locals_to_scrub.append((var_name, scrubbed_repr))
        
        # Replace sensitive variables in frame locals with safe placeholders
        for var_name, safe_repr in locals_to_scrub:
            try:
                del frame.f_locals[var_name]
            except Exception:
                pass
            scrubbed_vars.append(f"{var_name}={safe_repr}")
        
        tb = tb.tb_next
    
    # Force garbage collection to purge the deleted frame data from memory
    gc.collect()
    
    # Log the sanitized traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    sanitized_logger.critical(
        "UNHANDLED EXCEPTION (LGPD-sanitized traceback):\n%s",
        "".join(tb_lines)
    )
    
    if scrubbed_vars:
        sanitized_logger.critical(
            "LGPD: Scrubbed %d sensitive variables from traceback: %s",
            len(scrubbed_vars),
            ", ".join(scrubbed_vars)
        )


# Install sanitized exception hook (only in production — skip if SVISION_DEBUG is set)
if not os.getenv("SVISION_DEBUG"):
    sys.excepthook = _sanitized_excepthook
    logger.info("LGPD exception sanitizer installed (set SVISION_DEBUG=1 to disable)")


def _print_banner():
    """Prints startup banner with environment diagnostics."""
    import platform
    try:
        import torch
        cuda_status = f"CUDA {torch.version.cuda} — {torch.cuda.get_device_name(0)}" if torch.cuda.is_available() else "CPU only"
        torch_ver = torch.__version__
    except Exception:
        torch_ver = "not found"
        cuda_status = "unavailable"

    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║              SVision — Edge AI Backend                    ║
║              Copyright © 2026 Noxfort Systems                ║
╚══════════════════════════════════════════════════════════════╝
  Python   : {platform.python_version()}
  PyTorch  : {torch_ver}
  Compute  : {cuda_status}
  Platform : {platform.system()} {platform.release()}
"""
    print(banner)


def run_server():
    """
    Spins up the Uvicorn ASGI server hosting the FastAPI application.
    Binds to 0.0.0.0 to ensure accessibility across the local network.
    """
    _print_banner()
    logger.info("Initializing Uvicorn ASGI server on http://0.0.0.0:8000 ...")

    uvicorn.run(
        "src.api.core_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws="websockets",
        log_level="info",
    )

if __name__ == "__main__":
    run_server()
