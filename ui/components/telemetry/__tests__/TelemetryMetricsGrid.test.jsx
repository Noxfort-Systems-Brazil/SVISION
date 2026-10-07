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
 * File: TelemetryMetricsGrid.test.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Unit tests for TelemetryMetricsGrid component verifying KPI rendering and card clicks.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TelemetryMetricsGrid } from '../TelemetryMetricsGrid';

vi.mock('../../../contexts/LanguageContext', () => ({
    useTranslation: () => ({
        t: (key) => key
    })
}));

describe('TelemetryMetricsGrid', () => {
    const mockStats = {
        cpu_usage: 45,
        ram_usage: 62,
        vram_usage: 4500,
        fps_average: 60,
        fps_trend: { value: '+2.4', isPositive: true },
        temperature: 52,
        temp_trend: { value: '-1.0', isPositive: true },
        dropped_frames: 7,
        drops_trend: { value: '0.0', isPositive: true }
    };

    it('renders all 5 metric cards with formatted telemetry values', () => {
        render(<TelemetryMetricsGrid stats={mockStats} onSelectMetric={vi.fn()} />);

        expect(screen.getByText('CPU / RAM')).toBeInTheDocument();
        expect(screen.getByText('45% / 62%')).toBeInTheDocument();
        expect(screen.getByText('4.50 GB')).toBeInTheDocument();
        expect(screen.getByText('60')).toBeInTheDocument();
        expect(screen.getByText('52°C')).toBeInTheDocument();
        expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('fires onSelectMetric callback with metric details when card is clicked', () => {
        const onSelect = vi.fn();
        render(<TelemetryMetricsGrid stats={mockStats} onSelectMetric={onSelect} />);

        fireEvent.click(screen.getByText('CPU / RAM'));

        expect(onSelect).toHaveBeenCalledTimes(1);
        expect(onSelect).toHaveBeenCalledWith(
            expect.objectContaining({
                title: 'CPU / RAM Usage',
                value: '45% / 62%'
            })
        );
    });
});
