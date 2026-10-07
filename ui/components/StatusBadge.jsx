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
 * File: StatusBadge.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Visual status indicator pill component rendering badge variants for device states.
 */

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useTranslation } from '../contexts/LanguageContext';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export function StatusBadge({ status, className }) {
    const { t } = useTranslation();
    const isOnline = status === 'online';

    return (
        <span className={cn(
            "px-2 py-0.5 rounded-md text-xs font-semibold border inline-flex items-center gap-1.5",
            isOnline
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                : "bg-destructive/10 text-destructive-foreground border-destructive/20",
            className
        )}>
            {isOnline && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />}
            {isOnline ? t('status_online') : t('status_offline')}
        </span>
    );
}
