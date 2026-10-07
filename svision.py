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
#
# File: svision.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
SVision — Master Bootstrapper (Tauri v2 + Standard I/O IPC Architecture).

Primary entry point for the SVision platform.
Coordinates launching the Tauri v2 Desktop GUI or running in Headless Daemon mode.
"""

import sys
import os
import shutil
import signal
import platform
import subprocess

# ── Step 1: Environment and Virtualenv Auto-Resolution ─────────────

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["SVISION_ROOT"] = ROOT_DIR

if ROOT_DIR not in os.environ.get("PYTHONPATH", ""):
    os.environ["PYTHONPATH"] = f"{ROOT_DIR}:{os.environ.get('PYTHONPATH', '')}"

cargo_bin = os.path.expanduser("~/.cargo/bin")
current_path = os.environ.get("PATH", "")
if os.path.isdir(cargo_bin) and cargo_bin not in current_path:
    os.environ["PATH"] = f"{cargo_bin}:{current_path}"

# Auto-resolve Node v20+ from NVM if present
nvm_dir = os.path.expanduser("~/.nvm/versions/node")
if os.path.isdir(nvm_dir):
    try:
        versions = sorted(os.listdir(nvm_dir), reverse=True)
        for v in versions:
            nvm_bin = os.path.join(nvm_dir, v, "bin")
            if os.path.isdir(nvm_bin) and nvm_bin not in os.environ["PATH"]:
                os.environ["PATH"] = f"{nvm_bin}:{os.environ['PATH']}"
                break
    except Exception:
        pass

# Re-exec with .venv if run with system python
if sys.prefix == sys.base_prefix:
    venv_python = os.path.join(ROOT_DIR, ".venv", "bin", "python")
    if os.name == "nt":
        venv_python = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)

# Suppress noisy C++ library logs
os.environ.setdefault("OPENCV_FFMPEG_LOGLEVEL", "-8")
os.environ.setdefault("OPENCV_VIDEOIO_DEBUG", "0")
os.environ.setdefault("OPENCV_LOG_LEVEL", "FATAL")


# ── Step 2: Signal Handlers & Cleanup ───────────────────────────────

_synapse_proc = None


def _ensure_synapse_dispatcher():
    """Compiles (if needed) and spawns the Go Synapse Dispatcher process."""
    global _synapse_proc
    bin_path = os.path.join(ROOT_DIR, "bin", "synapse-dispatcher")
    go_src = os.path.join(ROOT_DIR, "svision-go")

    # If binary doesn't exist but Go source exists, compile it automatically
    if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
        go_compiler = shutil.which("go")
        if go_compiler and os.path.isdir(go_src):
            sys.stderr.write("[SVision] 🔨 Compiling Go Synapse Dispatcher...\n")
            try:
                subprocess.run(
                    [go_compiler, "build", "-C", go_src, "-o", bin_path, "."],
                    check=True,
                )
                sys.stderr.write("[SVision] ✅ Go Synapse Dispatcher compiled successfully.\n")
            except Exception as e:
                sys.stderr.write(f"[SVision] ⚠️ Failed to compile Go Synapse Dispatcher: {e}\n")

    # Start Go daemon in background if binary exists
    if os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
        try:
            sys.stderr.write(f"[SVision] 🚀 Starting Go Synapse Dispatcher ({bin_path})...\n")
            _synapse_proc = subprocess.Popen(
                [bin_path],
                stdout=subprocess.DEVNULL,
                stderr=sys.stderr,
            )
        except Exception as e:
            sys.stderr.write(f"[SVision] ⚠️ Failed to start Go Synapse Dispatcher: {e}\n")


def _hard_kill(signum, frame):
    """Immediate graceful shutdown handler."""
    sys.stderr.write("\n[SVision] Termination signal received. Exiting.\n")
    global _synapse_proc
    if _synapse_proc and _synapse_proc.poll() is None:
        try:
            _synapse_proc.terminate()
            _synapse_proc.wait(timeout=2.0)
        except Exception:
            _synapse_proc.kill()
    try:
        import gc
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, _hard_kill)
signal.signal(signal.SIGTERM, _hard_kill)


# ── Step 3: Desktop UI Launcher ────────────────────────────────────

def launch_desktop_ui():
    """
    Launches the modern desktop frontend (Tauri v2 + React).
    The Tauri runtime automatically spawns the Python StdioDaemon as its backend sidecar.
    """
    release_bin = os.path.join(ROOT_DIR, "src-tauri", "target", "release", "svision-cs-desktop")

    # 1. If release binary exists, execute it directly
    if os.path.isfile(release_bin) and os.access(release_bin, os.X_OK):
        sys.stderr.write(f"[SVision] 🚀 Launching compiled Desktop binary: {release_bin}\n")
        try:
            subprocess.run([release_bin])
        except KeyboardInterrupt:
            pass
        return

    # 2. Check if Cargo/Rust and npm are installed
    cargo_path = shutil.which("cargo")
    npm_path = shutil.which("npm")

    if not cargo_path:
        sys.stderr.write(
            "[SVision] ⚠️ Rust/Cargo não detectado no PATH.\n"
            "          Iniciando SVision em modo Headless Daemon...\n"
        )
        start_daemon()
        return

    # 3. Prepare clean environment (sanitize LD_LIBRARY_PATH and Snap overrides)
    clean_env = os.environ.copy()
    clean_env["SVISION_ROOT"] = ROOT_DIR
    clean_env["PYTHONPATH"] = ROOT_DIR
    clean_env["PYTHONUNBUFFERED"] = "1"
    clean_env["LD_LIBRARY_PATH"] = "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
    clean_env.pop("LD_PRELOAD", None)
    for key in list(clean_env.keys()):
        if key.startswith("SNAP") or "SNAP" in key:
            del clean_env[key]

    if os.path.isdir(cargo_bin) and cargo_bin not in clean_env.get("PATH", ""):
        clean_env["PATH"] = f"{cargo_bin}:{clean_env.get('PATH', '')}"

    # 4. Launch via npm run tauri -- dev
    if npm_path:
        sys.stderr.write("[SVision] ⚡ Booting SVision Desktop (Tauri v2 + React)...\n")
        try:
            subprocess.run(
                ["npm", "run", "tauri", "--", "dev"],
                cwd=ROOT_DIR,
                env=clean_env,
                check=True,
            )
            return
        except KeyboardInterrupt:
            sys.stderr.write("\n[SVision] Termination signal received. Exiting gracefully.\n")
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"[SVision] Error launching Tauri via npm: {e}\n")
            sys.exit(1)

    # 5. Fallback
    start_daemon()


def start_daemon():
    """Runs the Headless IPC Daemon."""
    from src.ipc.stdio_daemon import main as daemon_main
    daemon_main()


# ── Step 4: Entry Point ─────────────────────────────────────────────

def main():
    """Main launcher router."""
    sys.stderr.write(
        f"[SVision] SVision on {platform.system()} {platform.release()} "
        f"(Python {platform.python_version()}) [PID: {os.getpid()}]\n"
    )

    # Spawn Go Synapse Dispatcher network gatekeeper
    _ensure_synapse_dispatcher()

    args = sys.argv[1:]
    if "--daemon" in args or "--engine-core" in args or "--headless" in args or os.environ.get("SVISION_HEADLESS") == "1":
        sys.stderr.write("[SVision] Executing in Headless IPC Daemon mode...\n")
        start_daemon()
    else:
        launch_desktop_ui()


if __name__ == "__main__":
    main()
