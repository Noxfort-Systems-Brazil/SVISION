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
 * File: RecentOperationsTable.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Modular telemetry table displaying recent heuristic and pipeline operations.
 */

import React from 'react';
import { Cpu, Layers } from 'lucide-react';
import { useTranslation } from '../../contexts/LanguageContext';

const OPERATION_ICON_MAP = {
    'Heuristic Check': Cpu,
    default: Layers
};

const STATUS_STYLE_MAP = {
    'Completed': 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    'Failed': 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
    default: 'bg-secondary text-secondary-foreground border-border'
};

function getOperationIcon(name) {
    return OPERATION_ICON_MAP[name] || OPERATION_ICON_MAP.default;
}

function getStatusStyle(status) {
    return STATUS_STYLE_MAP[status] || STATUS_STYLE_MAP.default;
}

/**
 * Renders the recent engine operations table with declarative icon/status mappings.
 *
 * @param {Object} props
 * @param {Array<{ id: string, name: string, status: string }>} [props.operations=[]]
 * @param {Function} props.onSelectOperation - Callback triggered on row click
 */
export function RecentOperationsTable({ operations = [], onSelectOperation }) {
    const { t } = useTranslation();

    return (
        <div className="bg-card border border-border rounded-xl">
            <div className="border-b border-border px-4 py-3 flex items-center justify-between">
                <h4 className="text-sm font-medium text-card-foreground">{t('engine.recent_ops')}</h4>
                <button className="text-sm font-medium text-foreground border border-border bg-background px-3 py-1.5 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                    {t('engine.view_all')}
                </button>
            </div>
            <div className="p-4">
                <div className="flex items-center justify-between text-sm py-2 text-muted-foreground border-b border-border">
                    <span className="w-1/3">{t('engine.op_table_name')}</span>
                    <span className="w-1/3">{t('engine.op_table_status')}</span>
                    <span className="w-1/3 text-right">{t('engine.op_table_id')}</span>
                </div>

                {operations && operations.length > 0 ? (
                    operations.map((op, idx) => {
                        const Icon = getOperationIcon(op.name);
                        const statusStyle = getStatusStyle(op.status);

                        return (
                            <div
                                key={op.id || idx}
                                onClick={() => onSelectOperation?.({
                                    title: 'Operation Details',
                                    value: op.id,
                                    desc: `Full stack trace and parameter state for operation: ${op.name}`
                                })}
                                className={`flex items-center justify-between text-sm py-3 text-card-foreground cursor-pointer hover:bg-accent px-2 -mx-2 rounded-md transition-colors ${idx !== operations.length - 1 ? 'border-b border-border' : ''
                                    }`}
                            >
                                <span className="w-1/3 flex items-center gap-2 font-medium">
                                    <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
                                    <span className="truncate">{op.name}</span>
                                </span>
                                <span className="w-1/3">
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusStyle}`}>
                                        {op.status}
                                    </span>
                                </span>
                                <span className="w-1/3 text-right font-mono text-muted-foreground">{op.id}</span>
                            </div>
                        );
                    })
                ) : (
                    <div className="text-center text-sm text-muted-foreground py-4">{t('engine.no_ops')}</div>
                )}
            </div>
        </div>
    );
}
