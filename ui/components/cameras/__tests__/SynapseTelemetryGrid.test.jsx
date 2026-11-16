/*
 * SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
 * Copyright (C) 2026 Noxfort Systems
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * SPDX-FileCopyrightText: 2026 Noxfort Systems
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
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SynapseTelemetryGrid } from '../SynapseTelemetryGrid';

describe('SynapseTelemetryGrid', () => {
    it('renders waiting state when no telemetry exists', () => {
        render(<SynapseTelemetryGrid camera={{ id: 'cam_01' }} />);
        expect(screen.getByText(/Aguardando telemetria em tempo real/i)).toBeInTheDocument();
    });

    it('renders real fluid channels[] payload and calibration badge', () => {
        const camera = {
            id: 'cam_01',
            sensor_id: 'SP_REAL_01',
            calibrated: true,
            synapse: {
                camera_id: 'SP_REAL_01',
                timestamp: 1787196563800,
                calibrated: true,
                channels: [
                    { direction_deg: 115.0, speed: 45.2, density: 0.25 },
                    { direction_deg: 295.0, speed: 0.0, density: 0.0 },
                ],
            },
        };

        render(<SynapseTelemetryGrid camera={camera} />);

        expect(screen.getByText('Homografia Calibrada')).toBeInTheDocument();
        expect(screen.getByText(/Sensor:\s*SP_REAL_01/)).toBeInTheDocument();
        expect(screen.getByText('Canal 1')).toBeInTheDocument();
        expect(screen.getByText('45.2 km/h')).toBeInTheDocument();
        expect(screen.getByText('25.0%')).toBeInTheDocument();
        expect(screen.getByText('Nenhum fluxo transitando')).toBeInTheDocument();
    });

    it('renders uncalibrated warning when calibrated is false and preserves legacy traffic map', () => {
        const camera = {
            id: 'cam_legacy',
            synapse: {
                sensor_id: 'DEMO_01',
                calibrated: false,
                traffic: {
                    approach_1: { count: 12, speed_kmh: 50.0, occupancy: 0.3, density: 10.5 },
                },
            },
        };

        render(<SynapseTelemetryGrid camera={camera} />);

        expect(screen.getByText('Sem Homografia (Estimativa px)')).toBeInTheDocument();
        expect(screen.getByText('Via 1')).toBeInTheDocument();
        expect(screen.getByText('50.0 km/h')).toBeInTheDocument();
    });
});
