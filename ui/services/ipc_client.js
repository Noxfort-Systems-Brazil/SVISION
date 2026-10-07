/*
 * SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
 * Copyright (C) 2026 Noxfort Systems
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

class IPCClient {
    constructor() {
        /** @type {Map<string, Set<Function>>} */
        this._subscribers = new Map();
        this._lastDataTs = 0;
        this._active = false;
        this._backendError = null;
        this._camerasContext = [];
        this._unlisteners = [];

        this._boot();
    }

    // ── Bootstrap ──────────────────────────────────────────────────

    async _boot() {
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
        }
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
        this._camerasContext.push(cameraObject);
        this._dispatch('cameras', [...this._camerasContext]);
        this.sendCommand('add_camera', cameraObject);
    }

    removeCamera(cameraId) {
        this._camerasContext = this._camerasContext.filter((c) => c.id !== cameraId);
        this._dispatch('cameras', [...this._camerasContext]);
        this.sendCommand('remove_camera', { id: cameraId });
    }

    setCameras(importedList) {
        this._camerasContext = importedList;
        this._dispatch('cameras', [...this._camerasContext]);
        this.sendCommand('set_cameras', importedList);
    }

    updateSynapseConfig(config) {
        this.sendCommand('update_synapse_config', config);
    }

    // ── Status ─────────────────────────────────────────────────────

    get isActive() {
        return this._active;
    }

    get backendError() {
        return this._backendError;
    }

    get camerasContext() {
        return this._camerasContext;
    }
}

export const ipcClient = new IPCClient();
