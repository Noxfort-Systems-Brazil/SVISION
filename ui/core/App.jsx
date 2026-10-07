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
 * File: App.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Lean root wrapper uniting providers, sidebar, and content router.
 * All stateful logic has been extracted to dedicated hooks and components.
 */

import React, { useState } from 'react';
import { CamerasTab } from '../views/CamerasTab';
import { SVisionTab } from '../views/SVisionTab';
import { SynapseTab } from '../views/SynapseTab';
import { SettingsTab } from '../views/SettingsTab';
import { Sidebar } from '../components/Sidebar';
import { BackendErrorBanner } from '../components/BackendErrorBanner';
import { useConnectionStatus } from '../hooks/useConnectionStatus';
import { useTranslation } from '../contexts/LanguageContext';

// Providers
import { ThemeProvider } from '../contexts/ThemeContext';
import { LanguageProvider } from '../contexts/LanguageContext';

// Tab title resolution map
const TAB_TITLE_KEYS = {
    sensors: 'nav.sensors',
    engine: 'nav.engine',
    network: 'nav.network',
    settings: 'nav.settings',
};

// Connection status display config (IPC liveness: online/offline only)
const STATUS_CONFIG = {
    online: { color: 'bg-emerald-500', labelKey: 'status_online', animate: 'animate-pulse' },
    offline: { color: 'bg-red-500', label: 'Offline', animate: '' },
};

function AppContent() {
    const [activeTab, setActiveTab] = useState('sensors');
    const connectionStatus = useConnectionStatus();
    const { t } = useTranslation();

    const cs = STATUS_CONFIG[connectionStatus] || STATUS_CONFIG.offline;
    const statusLabel = cs.labelKey ? t(cs.labelKey) : cs.label;

    return (
        <div className="h-screen w-screen flex bg-background text-foreground overflow-hidden font-sans selection:bg-primary selection:text-primary-foreground">
            <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

            <main className="flex-1 bg-background flex flex-col relative overflow-hidden border-l border-border">
                {/* Header */}
                <header className="h-14 shrink-0 border-b border-border flex items-center px-8 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 sticky top-0">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{t('nav.workspace')}</span>
                        <span className="text-muted-foreground/50">/</span>
                        <span className="font-medium text-foreground">
                            {t(TAB_TITLE_KEYS[activeTab] || '')}
                        </span>
                    </div>
                    <div className="ml-auto flex items-center gap-4">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground bg-card px-3 py-1.5 rounded-md border border-border">
                            <span className={`w-1.5 h-1.5 rounded-full ${cs.color} ${cs.animate}`}></span>
                            {statusLabel}
                        </div>
                    </div>
                </header>

                <BackendErrorBanner />

                {/* Content Router */}
                <div className="flex-1 overflow-auto p-6 md:p-8 animate-in bg-background">
                    <div className="h-full w-full max-w-[1400px] mx-auto">
                        {activeTab === 'sensors' && <CamerasTab />}
                        {activeTab === 'engine' && <SVisionTab />}
                        {activeTab === 'network' && <SynapseTab />}
                        {activeTab === 'settings' && <SettingsTab />}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default function App() {
    return (
        <ThemeProvider>
            <LanguageProvider>
                <AppContent />
            </LanguageProvider>
        </ThemeProvider>
    );
}
