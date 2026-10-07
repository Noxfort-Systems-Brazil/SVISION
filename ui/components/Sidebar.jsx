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
 * File: Sidebar.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-30
 *
 * Description: Decoupled sidebar navigation component extracted from App.jsx (SRP).
 */

import React from 'react';
import { Cpu, Network, Video, Settings, LifeBuoy, MoreHorizontal } from 'lucide-react';
import { useTranslation } from '../contexts/LanguageContext';
import svisionLogo from '../assets/svision-logo.png';

function NavItem({ active, onClick, icon, label }) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-3 py-2 text-[13px] font-medium transition-colors outline-none rounded-md
                ${active
                    ? 'bg-accent text-accent-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                }
            `}
        >
            {icon}
            {label}
        </button>
    );
}

export function Sidebar({ activeTab, onTabChange }) {
    const { t } = useTranslation();

    return (
        <aside className="w-[240px] shrink-0 border-r border-border bg-card flex flex-col py-4">
            {/* Brand / Logo */}
            <div className="flex items-center gap-3 px-5 mb-6 cursor-default">
                <img
                    src={svisionLogo}
                    alt="SVision Logo"
                    className="w-8 h-8 object-contain drop-shadow-sm select-none"
                />
                <span className="text-sm font-semibold tracking-tight text-foreground">{t('app_name')}</span>
            </div>

            {/* Primary Nav Menu */}
            <nav className="flex flex-col space-y-0.5 px-3">
                <NavItem
                    active={activeTab === 'sensors'}
                    onClick={() => onTabChange('sensors')}
                    icon={<Video className="w-4 h-4" />}
                    label={t('nav.sensors')}
                />
                <NavItem
                    active={activeTab === 'engine'}
                    onClick={() => onTabChange('engine')}
                    icon={<Cpu className="w-4 h-4" />}
                    label={t('nav.engine')}
                />
                <NavItem
                    active={activeTab === 'network'}
                    onClick={() => onTabChange('network')}
                    icon={<Network className="w-4 h-4" />}
                    label={t('nav.network')}
                />
            </nav>

            {/* Bottom Settings Nav */}
            <div className="mt-auto px-3 flex flex-col space-y-0.5 mb-2">
                <NavItem
                    active={activeTab === 'settings'}
                    onClick={() => onTabChange('settings')}
                    icon={<Settings className="w-4 h-4" />}
                    label={t('nav.settings')}
                />
                <NavItem
                    active={false}
                    onClick={() => { }}
                    icon={<LifeBuoy className="w-4 h-4" />}
                    label={t('nav.help')}
                />
            </div>

            {/* User Profile Footer */}
            <div className="px-3">
                <div className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer transition-colors border border-transparent">
                    <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground">
                        N
                    </div>
                    <div className="flex flex-col flex-1">
                        <span className="text-[13px] font-medium text-foreground">Noxfort Edge</span>
                        <span className="text-[10px] text-muted-foreground line-clamp-1">moraes@noxfort.com</span>
                    </div>
                    <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                </div>
            </div>
        </aside>
    );
}
