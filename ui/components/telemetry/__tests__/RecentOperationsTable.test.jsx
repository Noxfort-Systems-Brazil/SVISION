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
 * File: RecentOperationsTable.test.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Unit tests for RecentOperationsTable verifying empty state, operation lists, and row clicks.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RecentOperationsTable } from '../RecentOperationsTable';

vi.mock('../../../contexts/LanguageContext', () => ({
    useTranslation: () => ({
        t: (key) => key
    })
}));

describe('RecentOperationsTable', () => {
    it('renders empty message when no operations are present', () => {
        render(<RecentOperationsTable operations={[]} onSelectOperation={vi.fn()} />);
        expect(screen.getByText('engine.no_ops')).toBeInTheDocument();
    });

    it('renders list of operations with status badges and triggers selection', () => {
        const mockOperations = [
            { id: 'op-001', name: 'Heuristic Check', status: 'Completed' },
            { id: 'op-002', name: 'Pipeline Sync', status: 'Failed' }
        ];
        const onSelect = vi.fn();

        render(<RecentOperationsTable operations={mockOperations} onSelectOperation={onSelect} />);

        expect(screen.getByText('Heuristic Check')).toBeInTheDocument();
        expect(screen.getByText('Completed')).toBeInTheDocument();
        expect(screen.getByText('op-001')).toBeInTheDocument();

        expect(screen.getByText('Pipeline Sync')).toBeInTheDocument();
        expect(screen.getByText('Failed')).toBeInTheDocument();
        expect(screen.getByText('op-002')).toBeInTheDocument();

        fireEvent.click(screen.getByText('Heuristic Check'));
        expect(onSelect).toHaveBeenCalledTimes(1);
        expect(onSelect).toHaveBeenCalledWith(
            expect.objectContaining({
                title: 'Operation Details',
                value: 'op-001'
            })
        );
    });
});
