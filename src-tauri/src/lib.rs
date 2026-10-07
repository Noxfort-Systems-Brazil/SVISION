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

// File: lib.rs
// Author: Gabriel Moraes
// Date: 2026-03-27

pub mod backend;

use backend::ipc::{get_backend_status, send_svision_command};
use backend::{kill_backend, spawn_python_backend, PythonProcessState};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let proc_state = PythonProcessState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }))
        .manage(proc_state)
        .setup(|app| {
            let handle = app.handle().clone();
            let state = app.state::<PythonProcessState>();
            spawn_python_backend(handle, &state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            send_svision_command,
            get_backend_status,
        ])
        .build(tauri::generate_context!())
        .expect("Error while building Tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                let state = app_handle.state::<PythonProcessState>();
                kill_backend(&state);
            }
        });
}
