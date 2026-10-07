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

// File: ipc.rs
// Author: Gabriel Moraes
// Date: 2026-03-27

use std::io::{BufRead, BufReader, Write};
use std::process::ChildStdout;
use tauri::{AppHandle, Emitter, State};
use super::state::{BackendStatus, PythonProcessState};

#[derive(serde::Serialize, serde::Deserialize, Clone, Debug)]
pub struct IpcCommandEnvelope {
    pub action: String,
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub payload: serde_json::Value,
}

#[derive(serde::Serialize, serde::Deserialize, Clone, Debug)]
pub struct BackendStatusInfo {
    pub status: BackendStatus,
    pub error: Option<String>,
}

#[tauri::command]
pub fn get_backend_status(state: State<'_, PythonProcessState>) -> Result<BackendStatusInfo, String> {
    let status = *state.status.lock().map_err(|e| e.to_string())?;
    let error = state.last_error.lock().map_err(|e| e.to_string())?.clone();
    Ok(BackendStatusInfo { status, error })
}

#[tauri::command]
pub fn send_svision_command(
    state: State<'_, PythonProcessState>,
    action: String,
    payload: Option<serde_json::Value>,
    id: Option<String>,
) -> Result<(), String> {
    let mut stdin_guard = state.stdin.lock().map_err(|e| e.to_string())?;

    if let Some(ref mut stdin) = *stdin_guard {
        let envelope = IpcCommandEnvelope {
            action: action.clone(),
            id: id.clone(),
            payload: payload.unwrap_or(serde_json::json!({})),
        };

        let json_str = serde_json::to_string(&envelope).map_err(|e| e.to_string())?;
        writeln!(stdin, "{}", json_str).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
        if action != "ping" {
            eprintln!("[Tauri IPC] 📤 Comando despachado: action='{}' (id={:?})", action, id);
        }
        Ok(())
    } else {
        let err_msg = if let Ok(err_guard) = state.last_error.lock() {
            if let Some(ref e) = *err_guard {
                format!("Python backend is unavailable: {}", e)
            } else {
                "Python backend process stdin is not available".to_string()
            }
        } else {
            "Python backend process stdin is not available".to_string()
        };
        eprintln!("[Tauri IPC] ❌ Falha: {}", err_msg);
        Err(err_msg)
    }
}

pub fn spawn_stdout_listener(stdout: ChildStdout, app_handle: AppHandle, state: PythonProcessState) {
    std::thread::spawn(move || {
        let mut first_message = true;
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.is_empty() {
                    continue;
                }

                if first_message {
                    first_message = false;
                    eprintln!("[Tauri IPC] 🟢 CONECTADO: Canal STDOUT com Core Python estabelecido com sucesso.");
                }

                if let Ok(value) = serde_json::from_str::<serde_json::Value>(trimmed) {
                    if let Some(obj) = value.as_object() {
                        let msg_type = obj.get("type").and_then(|v| v.as_str());
                        if msg_type == Some("event") {
                            if let Some(event_name) = obj.get("event").and_then(|v| v.as_str()) {
                                let topic = format!("svision:{}", event_name);
                                let data = obj.get("data").cloned().unwrap_or(serde_json::Value::Null);
                                let _ = app_handle.emit(&topic, data);
                            }
                        } else if msg_type == Some("response") {
                            let _ = app_handle.emit("svision:response", &value);
                        }
                    }
                } else {
                    eprintln!("[Tauri IPC] ⚠️ Linha não-JSON do Python: {}", trimmed);
                }
            }
        }
        eprintln!("[Tauri IPC] 🔴 DESCONECTADO: Canal STDOUT com Core Python foi encerrado.");

        let is_stopped = if let Ok(status) = state.status.lock() {
            *status == BackendStatus::Stopped
        } else {
            false
        };

        if !is_stopped {
            let err_msg = "Conexão com o backend Python foi encerrada inesperadamente.".to_string();
            if let Ok(mut status) = state.status.lock() {
                *status = BackendStatus::Failed;
            }
            if let Ok(mut last_err) = state.last_error.lock() {
                *last_err = Some(err_msg.clone());
            }
            let _ = app_handle.emit("svision:backend_error", serde_json::json!({
                "error": err_msg,
                "code": "PROCESS_UNEXPECTED_DISCONNECT"
            }));
        }
    });
}

