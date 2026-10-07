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
 * File: MetricCard.test.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Unit tests for MetricCard component verifying title, value, trends, and click behavior.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
    it('renders title, value, and description correctly', () => {
        render(
            <MetricCard
                title="Total Vehicles"
                value="1,420"
                desc="Measured in last 60 minutes"
            />
        );

        expect(screen.getByText('Total Vehicles')).toBeInTheDocument();
        expect(screen.getByText('1,420')).toBeInTheDocument();
        expect(screen.getByText('Measured in last 60 minutes')).toBeInTheDocument();
    });

    it('renders positive trend badge with emerald styling', () => {
        render(
            <MetricCard
                title="Inference Speed"
                value="120 FPS"
                trend="+12%"
                positive={true}
            />
        );

        const trendBadge = screen.getByText('+12%');
        expect(trendBadge).toBeInTheDocument();
        expect(trendBadge).toHaveClass('text-emerald-600');
    });

    it('renders negative/neutral trend badge', () => {
        render(
            <MetricCard
                title="VRAM Usage"
                value="4,200 MB"
                trend="-5%"
                positive={false}
            />
        );

        const trendBadge = screen.getByText('-5%');
        expect(trendBadge).toBeInTheDocument();
        expect(trendBadge).toHaveClass('text-muted-foreground');
    });

    it('handles onClick callback when clicked', () => {
        const handleClick = vi.fn();
        render(
            <MetricCard
                title="Clickable Metric"
                value="42"
                onClick={handleClick}
            />
        );

        fireEvent.click(screen.getByText('Clickable Metric'));
        expect(handleClick).toHaveBeenCalledTimes(1);
    });
});
