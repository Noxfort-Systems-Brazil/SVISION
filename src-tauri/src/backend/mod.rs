// SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
// Copyright (C) 2026 Noxfort Systems
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// File: mod.rs
// Author: Gabriel Moraes
// Date: 2026-03-27

pub mod state;
pub mod ipc;

pub use state::{BackendStatus, PythonProcessState};
pub use ipc::{get_backend_status, send_svision_command};

use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};
use tauri::{AppHandle, Emitter};

pub fn find_project_root() -> PathBuf {
    if let Ok(root_env) = std::env::var("SVISION_ROOT") {
        let p = PathBuf::from(root_env);
        if p.exists() {
            return p;
        }
    }

    let mut cur = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    for _ in 0..8 {
        if cur.join("svision.py").exists() || cur.join("src/ipc/stdio_daemon.py").exists() {
            return cur;
        }
        if let Some(parent) = cur.parent() {
            cur = parent.to_path_buf();
        } else {
            break;
        }
    }

    if let Ok(exe) = std::env::current_exe() {
        let mut cur = exe;
        for _ in 0..8 {
            if cur.join("svision.py").exists() || cur.join("src/ipc/stdio_daemon.py").exists() {
                return cur;
            }
            if let Some(parent) = cur.parent() {
                cur = parent.to_path_buf();
            } else {
                break;
            }
        }
    }

    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
}

pub fn resolve_python_binary(root: &PathBuf) -> String {
    if let Ok(custom_py) = std::env::var("SVISION_PYTHON") {
        let p = PathBuf::from(&custom_py);
        if p.exists() {
            return custom_py;
        }
    }

    if let Ok(venv_env) = std::env::var("VIRTUAL_ENV") {
        let venv_path = PathBuf::from(venv_env);
        let candidates = [
            venv_path.join("bin/python3"),
            venv_path.join("bin/python"),
            venv_path.join("Scripts/python.exe"),
        ];
        for candidate in &candidates {
            if candidate.exists() {
                return candidate.to_string_lossy().to_string();
            }
        }
    }

    let candidates = [
        root.join(".venv/bin/python3"),
        root.join(".venv/bin/python"),
        root.join("venv/bin/python3"),
        root.join("venv/bin/python"),
        root.join(".venv/Scripts/python.exe"),
        root.join("venv/Scripts/python.exe"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            return candidate.to_string_lossy().to_string();
        }
    }

    "python3".to_string()
}

pub fn spawn_python_backend(app_handle: AppHandle, state: &PythonProcessState) {
    let root = find_project_root();
    let python_bin = resolve_python_binary(&root);

    eprintln!("[Tauri] 🚀 Invocando backend Python: '{}' no diretório '{:?}'", python_bin, root);

    let mut child = match Command::new(&python_bin)
        .args(["svision.py", "--daemon"])
        .env("PYTHONUNBUFFERED", "1")
        .env("PYTHONPATH", &root)
        .env_remove("LD_LIBRARY_PATH")
        .env_remove("LD_PRELOAD")
        .current_dir(&root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
    {
        Ok(c) => {
            eprintln!("[Tauri] ✅ Processo Python iniciado com sucesso (PID: {})", c.id());
            if let Ok(mut status_guard) = state.status.lock() {
                *status_guard = BackendStatus::Running;
            }
            c
        }
        Err(e) => {
            let err_msg = format!("Falha ao iniciar processo Python ('{}' em {:?}): {}", python_bin, root, e);
            eprintln!("[Tauri] ❌ {}", err_msg);
            if let Ok(mut status_guard) = state.status.lock() {
                *status_guard = BackendStatus::Failed;
            }
            if let Ok(mut err_guard) = state.last_error.lock() {
                *err_guard = Some(err_msg.clone());
            }
            let _ = app_handle.emit("svision:backend_error", serde_json::json!({
                "error": err_msg,
                "code": "SPAWN_FAILED",
                "python_bin": python_bin,
                "root": root.to_string_lossy(),
            }));
            return;
        }
    };

    if let Some(stdin) = child.stdin.take() {
        let mut stdin_guard = state.stdin.lock().unwrap();
        *stdin_guard = Some(stdin);
    }

    let stdout = child.stdout.take().expect("Failed to open child stdout");
    {
        let mut proc_guard = state.process.lock().unwrap();
        *proc_guard = Some(child);
    }

    ipc::spawn_stdout_listener(stdout, app_handle, state.clone());
}

pub fn kill_backend(state: &PythonProcessState) {
    if let Ok(mut status_guard) = state.status.lock() {
        *status_guard = BackendStatus::Stopped;
    }

    // 1. Close STDIN to signal Python daemon that the parent IPC channel is closing.
    // In src/ipc/stdio_daemon.py, EOF on STDIN triggers _on_disconnect -> shutdown().
    if let Ok(mut stdin_guard) = state.stdin.lock() {
        if let Some(mut stdin) = stdin_guard.take() {
            let _ = std::io::Write::flush(&mut stdin);
            drop(stdin);
        }
    }

    // 2. Take process handle to perform graceful shutdown and reap zombie.
    if let Ok(mut proc_guard) = state.process.lock() {
        if let Some(mut child) = proc_guard.take() {
            let pid = child.id();
            eprintln!("[Tauri] 🛑 Solicitando encerramento gracioso do Python (PID: {})...", pid);

            // 3. On Unix, send SIGTERM so Python can clean GPU memory (torch.cuda.empty_cache()).
            #[cfg(unix)]
            {
                unsafe {
                    libc::kill(pid as libc::pid_t, libc::SIGTERM);
                }
            }

            // 4. Wait for graceful exit with timeout (up to 2.5 seconds).
            let wait_timeout = Duration::from_millis(2500);
            let poll_interval = Duration::from_millis(50);
            let start = Instant::now();
            let mut exited = false;

            while start.elapsed() < wait_timeout {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        eprintln!("[Tauri] ✅ Backend Python finalizou graciosamente (status: {}).", status);
                        exited = true;
                        break;
                    }
                    Ok(None) => {
                        std::thread::sleep(poll_interval);
                    }
                    Err(e) => {
                        eprintln!("[Tauri] ⚠️ Erro ao verificar status do processo Python: {}", e);
                        break;
                    }
                }
            }

            // 5. If process did not exit in time, send SIGKILL as fallback.
            if !exited {
                eprintln!("[Tauri] ⚠️ Backend Python não encerrou no tempo limite. Forçando SIGKILL...");
                let _ = child.kill();
                // 6. Always call wait() to reap process from kernel process table (prevents defunct/zombie).
                match child.wait() {
                    Ok(status) => {
                        eprintln!("[Tauri] 🛑 Processo Python finalizado forçadamente e recolhido (status: {}).", status);
                    }
                    Err(e) => {
                        eprintln!("[Tauri] ❌ Erro ao aguardar término do processo: {}", e);
                    }
                }
            }
        }
    }
}
