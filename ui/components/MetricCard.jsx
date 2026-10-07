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
 * File: MetricCard.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Reusable and interactive metric display card component supporting badges, trends, and click actions.
 */

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const MetricCard = React.memo(function MetricCard({
    title,
    value,
    desc,
    description,
    trend,
    positive,
    onClick,
    className = ''
}) {
    const text = desc || description;
    const hasBadgeTrend = trend && positive !== undefined;
    const hasInlineTrend = trend && positive === undefined;
    const isClickable = typeof onClick === 'function';

    return (
        <div
            onClick={onClick}
            className={`bg-card border border-border rounded-xl p-5 md:p-6 flex flex-col justify-between hover:bg-accent transition-all shadow-sm group ${
                isClickable ? 'cursor-pointer' : ''
            } ${className}`}
        >
            <div className="flex flex-col gap-1 mb-4">
                <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">{title}</h4>
                    {hasBadgeTrend && (
                        <div className={`px-2 py-0.5 rounded-md text-xs font-semibold flex items-center gap-1 ${
                            positive
                                ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10'
                                : 'text-muted-foreground bg-secondary'
                        }`}>
                            {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {trend}
                        </div>
                    )}
                </div>
                <div className="text-2xl md:text-3xl font-bold tracking-tight text-card-foreground mt-2">{value}</div>
            </div>

            {text && (
                <div className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                    {hasInlineTrend && <span className="text-foreground mr-1">{trend}</span>}
                    <span>{text}</span>
                </div>
            )}
        </div>
    );
});

export default MetricCard;
