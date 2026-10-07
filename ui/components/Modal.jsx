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
 * File: Modal.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Accessible modal dialog wrapper featuring animated entrance, backdrop blur, and keyboard dismissal.
 */

import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

export function Modal({ isOpen, onClose, title, subtitle, children }) {
    const [isRendered, setIsRendered] = useState(false);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setIsRendered(true);
            setTimeout(() => setIsVisible(true), 10);
        } else {
            setIsVisible(false);
            setTimeout(() => setIsRendered(false), 200);
        }
    }, [isOpen]);

    useEffect(() => {
        function handleKeyDown(e) {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        }
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isRendered) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto">
            {/* Backdrop */}
            <div
                className={`absolute inset-0 bg-background/80 backdrop-blur-sm transition-opacity duration-200 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
                onClick={onClose}
            />

            {/* Modal Box */}
            <div
                className={`relative bg-card border border-border shadow-lg rounded-xl w-full max-w-lg mx-4 flex flex-col overflow-hidden transition-all duration-200 transform
                    ${isVisible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-4'}
                `}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/40">
                    <div>
                        <h2 className="text-lg font-semibold tracking-tight text-card-foreground line-clamp-1">{title}</h2>
                        {subtitle && <p className="text-sm text-muted-foreground mt-0.5 line-clamp-1">{subtitle}</p>}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors ml-4 shrink-0"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[70vh]">
                    {children}
                </div>

                {/* Subtle Footer */}
                <div className="px-6 py-3 border-t border-border bg-muted/20 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-background border border-border text-foreground hover:bg-accent rounded-md text-sm font-medium transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
