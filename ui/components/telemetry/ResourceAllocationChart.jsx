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
 * File: ResourceAllocationChart.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Dedicated component for resource allocation telemetry chart and timeframe controls.
 */

import React, { useState } from 'react';
import { EChart } from '../EChart';
import { useTranslation } from '../../contexts/LanguageContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useResourceChartOptions } from '../../hooks/useResourceChartOptions';

/**
 * Renders the resource allocation telemetry chart with timeframe filtering controls.
 *
 * @param {Object} props
 * @param {number[]} [props.cpuHistory=[]]
 * @param {number[]} [props.ramHistory=[]]
 * @param {number[]} [props.vramHistory=[]]
 */
export function ResourceAllocationChart({ cpuHistory = [], ramHistory = [], vramHistory = [] }) {
    const { t } = useTranslation();
    const { theme } = useTheme();
    const [selectedRange, setSelectedRange] = useState('3m');

    const chartOptions = useResourceChartOptions({
        cpuHistory,
        ramHistory,
        vramHistory,
        theme
    });

    const filterRanges = [
        { id: '3m', label: t('engine.last_3_months') },
        { id: '30d', label: t('engine.last_30_days') },
        { id: '7d', label: t('engine.last_7_days') }
    ];

    return (
        <div className="flex-1 bg-card border border-border rounded-xl p-6 flex flex-col justify-between">
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="text-base font-semibold text-card-foreground mb-1">{t('engine.resource_allocation')}</h3>
                    <p className="text-sm text-muted-foreground">{t('engine.resource_desc')}</p>
                </div>
                <div className="flex items-center rounded-md border border-border bg-background p-1">
                    {filterRanges.map(range => (
                        <button
                            key={range.id}
                            onClick={() => setSelectedRange(range.id)}
                            className={`px-3 py-1 text-xs font-medium rounded-sm transition-colors ${selectedRange === range.id
                                ? 'text-foreground bg-accent'
                                : 'text-muted-foreground hover:text-foreground'
                                }`}
                        >
                            {range.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 w-full min-h-[300px] mt-6 relative opacity-80 mix-blend-screen">
                <EChart
                    option={chartOptions}
                    style={{ height: '100%', width: '100%', position: 'absolute', bottom: 0 }}
                />
            </div>
        </div>
    );
}
