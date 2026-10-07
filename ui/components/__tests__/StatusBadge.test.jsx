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
 * File: StatusBadge.test.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Unit tests for StatusBadge component verifying state rendering and styling.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../StatusBadge';
import { LanguageProvider } from '../../contexts/LanguageContext';

function renderWithProviders(ui) {
    return render(<LanguageProvider>{ui}</LanguageProvider>);
}

describe('StatusBadge', () => {
    it('renders online badge with emerald styling and pulse dot', () => {
        renderWithProviders(<StatusBadge status="online" />);

        const badge = screen.getByText(/online/i);
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveClass('text-emerald-600');
    });

    it('renders offline badge with destructive styling and no pulse dot', () => {
        renderWithProviders(<StatusBadge status="offline" />);

        const badge = screen.getByText(/offline/i);
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveClass('text-destructive-foreground');
    });

    it('merges custom className correctly', () => {
        renderWithProviders(<StatusBadge status="online" className="custom-test-class" />);

        const badge = screen.getByText(/online/i);
        expect(badge).toHaveClass('custom-test-class');
    });
});
