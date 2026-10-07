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

// File: state.rs
// Author: Gabriel Moraes
// Date: 2026-03-27

use std::process::{Child, ChildStdin};
use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Copy, PartialEq, Eq, Debug)]
#[serde(rename_all = "snake_case")]
pub enum BackendStatus {
    Starting,
    Running,
    Failed,
    Stopped,
}

#[derive(Clone)]
pub struct PythonProcessState {
    pub stdin: Arc<Mutex<Option<ChildStdin>>>,
    pub process: Arc<Mutex<Option<Child>>>,
    pub status: Arc<Mutex<BackendStatus>>,
    pub last_error: Arc<Mutex<Option<String>>>,
}

impl PythonProcessState {
    pub fn new() -> Self {
        Self {
            stdin: Arc::new(Mutex::new(None)),
            process: Arc::new(Mutex::new(None)),
            status: Arc::new(Mutex::new(BackendStatus::Starting)),
            last_error: Arc::new(Mutex::new(None)),
        }
    }
}

impl Default for PythonProcessState {
    fn default() -> Self {
        Self::new()
    }
}

