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
 * File: useNetworkLatency.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Subscribes to 'network_latency' telemetry via IPC.
 * Uses requestAnimationFrame coalescing to batch high-frequency updates.
 */
import { useState, useEffect, useRef } from 'react';
import { ipcClient } from '../services/ipc_client';

export function useNetworkLatency() {
    const [latencyHistory, setLatencyHistory] = useState([]);
    const pendingData = useRef([]);
    const frameId = useRef(null);

    useEffect(() => {
        const updateState = () => {
            if (pendingData.current.length > 0) {
                const newItems = [...pendingData.current];
                pendingData.current = [];

                setLatencyHistory(prev => {
                    const newHistory = [...prev, ...newItems];
                    if (newHistory.length > 50) return newHistory.slice(-50);
                    return newHistory;
                });
            }
            frameId.current = requestAnimationFrame(updateState);
        };

        frameId.current = requestAnimationFrame(updateState);

        const unsubscribe = ipcClient.subscribe('network_latency', (data) => {
            pendingData.current.push(data);
        });

        return () => {
            unsubscribe();
            if (frameId.current) cancelAnimationFrame(frameId.current);
        };
    }, []);

    return latencyHistory;
}
