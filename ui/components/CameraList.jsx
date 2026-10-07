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
 * File: CameraList.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Interactive sidebar list component for searching, filtering, and selecting camera streams.
 */

import React, { useState, useMemo } from 'react';
import { StatusBadge } from './StatusBadge';
import { useTranslation } from '../contexts/LanguageContext';
import { Search, X } from 'lucide-react';

export function CameraList({ cameras = [], onSelect, selectedId }) {
    const { t } = useTranslation();
    const [searchQuery, setSearchQuery] = useState('');

    const filteredCameras = useMemo(() => {
        if (!searchQuery.trim()) return cameras;
        const q = searchQuery.toLowerCase().trim();
        return cameras.filter(cam => {
            const nameMatch = cam.name?.toLowerCase().includes(q);
            const idMatch = cam.id?.toString().toLowerCase().includes(q);
            const portMatch = cam.synapse_port?.toString().includes(q);
            const statusMatch = cam.status?.toLowerCase().includes(q);
            return nameMatch || idMatch || portMatch || statusMatch;
        });
    }, [cameras, searchQuery]);

    return (
        <>
            <div className="p-4 border-b border-border shrink-0 bg-background/50">
                <h2 className="text-sm font-semibold text-card-foreground flex items-center justify-between">
                    {t('sensors.library')}
                </h2>
                <div className="relative mt-4">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder={t('sensors.search_ph')}
                        className="w-full bg-card border border-border rounded-md pl-9 pr-8 py-2 text-xs text-foreground focus:outline-none focus:border-ring placeholder:text-muted-foreground"
                    />
                    {searchQuery && (
                        <button
                            type="button"
                            onClick={() => setSearchQuery('')}
                            className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                {filteredCameras.map(cam => (
                    <button
                        key={cam.id}
                        onClick={() => onSelect(cam.id)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors flex flex-col gap-1 border
                            ${selectedId === cam.id
                                ? 'bg-accent/80 border-border text-foreground'
                                : 'bg-transparent border-transparent hover:bg-accent/40 text-muted-foreground'
                            }
                        `}
                    >
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium line-clamp-1">{cam.name}</span>
                            <StatusBadge status={cam.status} />
                        </div>
                        <div className="text-xs text-muted-foreground font-medium flex items-center justify-between">
                            <span>{cam.fps} FPS • {cam.scs}% SCS</span>
                            {cam.synapse_port && (
                                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                    :{cam.synapse_port}
                                </span>
                            )}
                        </div>
                    </button>
                ))}

                {cameras.length === 0 && (
                    <div className="p-6 text-center text-sm text-muted-foreground">
                        {t('sensors.no_active')}
                    </div>
                )}

                {cameras.length > 0 && filteredCameras.length === 0 && (
                    <div className="p-6 text-center text-xs text-muted-foreground">
                        {t('sensors.no_results') || 'No cameras match your search.'}
                    </div>
                )}
            </div>
        </>
    );
}
