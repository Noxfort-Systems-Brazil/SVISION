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
 * File: useEngineStats.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Subscribes to 'engine_stats' telemetry via IPC and maintains
 * rolling history arrays for VRAM, CPU, and RAM sparklines.
 * Uses requestAnimationFrame coalescing to prevent render thrashing.
 */
import { useState, useEffect, useRef } from 'react';
import { ipcClient } from '../services/ipc_client';

export function useEngineStats() {
    const [stats, setStats] = useState({
        cpu_usage: 0,
        ram_usage: 0,
        vram_usage: 0,
        vram_trend: { value: "0%", isPositive: true },
        temperature: 0,
        temp_trend: { value: "0%", isPositive: true },
        fps_average: 0,
        fps_trend: { value: "0%", isPositive: true },
        dropped_frames: 0,
        drops_trend: { value: "0%", isPositive: true },
        active_gear: 'Nano',
        recent_operations: [],
        vram_history: Array(20).fill(0),
        cpu_history: Array(20).fill(0),
        ram_history: Array(20).fill(0)
    });

    const pendingData = useRef(null);
    const frameId = useRef(null);

    useEffect(() => {
        const updateState = () => {
            if (pendingData.current) {
                const data = pendingData.current;
                pendingData.current = null;

                setStats(prev => {
                    const newVramHistory = [...(prev.vram_history || Array(20).fill(0)).slice(1), data.vram_usage || 0];
                    const newCpuHistory = [...(prev.cpu_history || Array(20).fill(0)).slice(1), data.cpu_usage || 0];
                    const newRamHistory = [...(prev.ram_history || Array(20).fill(0)).slice(1), data.ram_usage || 0];

                    return {
                        ...prev,
                        ...data,
                        vram_history: newVramHistory,
                        cpu_history: newCpuHistory,
                        ram_history: newRamHistory
                    };
                });
            }
            frameId.current = requestAnimationFrame(updateState);
        };

        frameId.current = requestAnimationFrame(updateState);

        const unsubscribe = ipcClient.subscribe('engine_stats', (data) => {
            pendingData.current = data;
        });

        return () => {
            unsubscribe();
            if (frameId.current) cancelAnimationFrame(frameId.current);
        };
    }, []);

    return stats;
}
