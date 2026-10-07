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
 * File: useResourceChartOptions.js
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Custom hook encapsulating ECharts option construction and theme color resolution for resource telemetry.
 */

import { useMemo } from 'react';

/**
 * Hook to build memoized ECharts configuration for the resource allocation timeline.
 *
 * @param {Object} params
 * @param {number[]} [params.cpuHistory=[]]
 * @param {number[]} [params.ramHistory=[]]
 * @param {number[]} [params.vramHistory=[]]
 * @param {string} params.theme - Current theme ('dark' | 'light')
 * @returns {Object} ECharts options object
 */
export function useResourceChartOptions({ cpuHistory = [], ramHistory = [], vramHistory = [], theme }) {
    // Canvas API cannot natively parse var(--color) in addColorStop, so we resolve explicit hex colors.
    const cardBg = theme === 'dark' ? '#09090b' : '#ffffff';
    const borderColor = theme === 'dark' ? '#27272a' : '#e4e4e7';
    const cardFg = theme === 'dark' ? '#fafafa' : '#09090b';

    return useMemo(() => ({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: cardBg,
            borderColor: borderColor,
            textStyle: { color: cardFg }
        },
        legend: {
            data: ['CPU (%)', 'RAM (%)', 'VRAM (MB)'],
            textStyle: { color: cardFg },
            icon: 'circle'
        },
        grid: { left: '2%', right: '2%', bottom: '5%', top: '15%', containLabel: true },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: Array.from({ length: 20 }, (_, i) => `T-${19 - i}s`),
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { show: false }
        },
        yAxis: [
            {
                type: 'value',
                name: 'Percentage',
                min: 0,
                max: 100,
                splitLine: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: 'gray' }
            },
            {
                type: 'value',
                name: 'MB',
                splitLine: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: 'gray' }
            }
        ],
        series: [
            {
                name: 'CPU (%)',
                type: 'line',
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: '#3b82f6' }, // Blue
                data: cpuHistory
            },
            {
                name: 'RAM (%)',
                type: 'line',
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: '#10b981' }, // Emerald
                data: ramHistory
            },
            {
                name: 'VRAM (MB)',
                type: 'line',
                yAxisIndex: 1,
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: '#8b5cf6' }, // Violet
                areaStyle: {
                    color: {
                        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: '#8b5cf6' },
                            { offset: 1, color: 'transparent' }
                        ]
                    }
                },
                data: vramHistory
            }
        ]
    }), [cpuHistory, ramHistory, vramHistory, cardBg, borderColor, cardFg]);
}
