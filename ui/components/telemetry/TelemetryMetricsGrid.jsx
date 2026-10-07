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
 * File: TelemetryMetricsGrid.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Modular KPI metrics grid component displaying real-time engine telemetry cards.
 */

import React, { useMemo } from 'react';
import { MetricCard } from '../MetricCard';
import { useTranslation } from '../../contexts/LanguageContext';

/**
 * Renders the top KPI metrics grid for hardware and engine telemetry.
 *
 * @param {Object} props
 * @param {Object} props.stats - Telemetry stats from useEngineStats
 * @param {Function} props.onSelectMetric - Callback invoked when a KPI card is clicked
 */
export function TelemetryMetricsGrid({ stats, onSelectMetric }) {
    const { t } = useTranslation();

    const metrics = useMemo(() => [
        {
            id: 'cpu_ram',
            title: 'CPU / RAM',
            value: `${stats?.cpu_usage || 0}% / ${stats?.ram_usage || 0}%`,
            trend: 'Live',
            description: 'System Processor and Memory Utilization',
            positive: (stats?.cpu_usage || 0) < 80,
            detail: {
                title: 'CPU / RAM Usage',
                value: `${stats?.cpu_usage || 0}% / ${stats?.ram_usage || 0}%`,
                desc: 'Real-time aggregated physical CPU cores load and active System Memory block sizes.'
            }
        },
        {
            id: 'vram',
            title: t('engine.vram_usage'),
            value: `${((stats?.vram_usage || 0) / 1000).toFixed(2)} GB`,
            trend: 'Live',
            description: t('engine.vram_desc'),
            positive: true,
            detail: {
                title: t('engine.vram_usage'),
                value: `${((stats?.vram_usage || 0) / 1000).toFixed(2)} GB`,
                desc: 'Deep memory allocation inspection over node 1 and node 2.'
            }
        },
        {
            id: 'fps',
            title: t('engine.fps'),
            value: (stats?.fps_average ?? 0).toString(),
            trend: stats?.fps_trend?.value || '0.0',
            description: t('engine.fps_desc'),
            positive: Boolean(stats?.fps_trend?.isPositive),
            detail: {
                title: t('engine.fps'),
                value: `${stats?.fps_average ?? 0} FPS`,
                desc: 'Average Frames Per Second across all active heuristic engines.'
            }
        },
        {
            id: 'temp',
            title: t('engine.temp'),
            value: `${stats?.temperature ?? 0}°C`,
            trend: stats?.temp_trend?.value || '0.0',
            description: t('engine.temp_desc'),
            positive: Boolean(stats?.temp_trend?.isPositive),
            detail: {
                title: t('engine.temp'),
                value: `${stats?.temperature ?? 0}°C`,
                desc: 'Thermal diode readout from primary compute unit.'
            }
        },
        {
            id: 'drops',
            title: t('engine.drops'),
            value: (stats?.dropped_frames ?? 0).toString(),
            trend: stats?.drops_trend?.value || '0.0',
            description: t('engine.drops_desc'),
            positive: Boolean(stats?.drops_trend?.isPositive),
            detail: {
                title: t('engine.drops'),
                value: `${stats?.dropped_frames ?? 0}`,
                desc: 'Frames lost due to processing queue overflow or thermal throttling.'
            }
        }
    ], [stats, t]);

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
            {metrics.map((metric) => (
                <MetricCard
                    key={metric.id}
                    title={metric.title}
                    value={metric.value}
                    trend={metric.trend}
                    description={metric.description}
                    positive={metric.positive}
                    onClick={() => onSelectMetric?.(metric.detail)}
                />
            ))}
        </div>
    );
}
