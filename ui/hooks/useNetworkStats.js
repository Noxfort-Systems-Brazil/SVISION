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
 * File: useNetworkStats.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Subscribes to 'network_stats' telemetry via IPC.
 */
import { useState, useEffect } from 'react';
import { ipcClient } from '../services/ipc_client';

export function useNetworkStats() {
    const [stats, setStats] = useState({
        active_connections: 0,
        conn_trend: "0%",
        packet_delivery: "0.00",
        delivery_trend: "Stable",
        bandwidth_peak: 0,
        bandwidth_trend: "0%"
    });

    useEffect(() => {
        const unsubscribe = ipcClient.subscribe('network_stats', (data) => {
            setStats(data);
        });
        return unsubscribe;
    }, []);

    return stats;
}
