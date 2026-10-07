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
 * File: SVisionTab.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Core telemetry dashboard orchestrating engine metrics, resource usage charts, and hardware gauges.
 */

import React, { useState } from 'react';
import { useEngineStats } from '../hooks/useEngineStats';
import { TelemetryMetricsGrid } from '../components/telemetry/TelemetryMetricsGrid';
import { ResourceAllocationChart } from '../components/telemetry/ResourceAllocationChart';
import { RecentOperationsTable } from '../components/telemetry/RecentOperationsTable';
import { MetricDetailModal } from '../components/telemetry/MetricDetailModal';

/**
 * Orchestrator view for real-time engine telemetry, resource charts, and pipeline operations.
 */
export function SVisionTab() {
    const stats = useEngineStats();
    const [selectedMetric, setSelectedMetric] = useState(null);

    return (
        <div className="h-full flex flex-col space-y-4">
            {/* Top Cards Grid */}
            <TelemetryMetricsGrid
                stats={stats}
                onSelectMetric={setSelectedMetric}
            />

            {/* Main Graph Area */}
            <ResourceAllocationChart
                cpuHistory={stats.cpu_history}
                ramHistory={stats.ram_history}
                vramHistory={stats.vram_history}
            />

            {/* Recent Operations Table */}
            <RecentOperationsTable
                operations={stats.recent_operations}
                onSelectOperation={setSelectedMetric}
            />

            {/* Deep Dive Inspection Modal */}
            <MetricDetailModal
                metric={selectedMetric}
                onClose={() => setSelectedMetric(null)}
            />
        </div>
    );
}
