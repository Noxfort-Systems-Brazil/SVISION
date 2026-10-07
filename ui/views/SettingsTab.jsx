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
 * File: SettingsTab.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Settings view for configuring user preferences, language selection, and UI theme.
 */

import React from 'react';
import { useTranslation } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { Globe, Palette } from 'lucide-react';

export function SettingsTab() {
    const { language, setLanguage, t } = useTranslation();
    const { theme, setTheme } = useTheme();

    return (
        <div className="h-full flex flex-col space-y-8 animate-in mt-4">
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('settings.title')}</h1>
                <p className="text-muted-foreground mt-1">{t('settings.subtitle')}</p>
            </div>

            <div className="flex flex-col gap-6 max-w-2xl">
                {/* General Settings */}
                <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
                    <div className="px-6 py-4 border-b border-border bg-muted/50">
                        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                            <Globe className="w-4 h-4 text-muted-foreground" />
                            {t('settings.general_title')}
                        </h2>
                    </div>
                    <div className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <label className="text-sm font-medium text-foreground">{t('settings.lang_label')}</label>
                                <p className="text-xs text-muted-foreground mt-1 max-w-sm">{t('settings.lang_desc')}</p>
                            </div>
                            <select
                                value={language}
                                onChange={(e) => setLanguage(e.target.value)}
                                className="bg-background border border-border text-sm rounded-md px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                            >
                                <option value="pt_br">Português (BR)</option>
                                <option value="en_us">English (US)</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Appearance Settings */}
                <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
                    <div className="px-6 py-4 border-b border-border bg-muted/50">
                        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                            <Palette className="w-4 h-4 text-muted-foreground" />
                            {t('settings.appearance_title')}
                        </h2>
                    </div>
                    <div className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <label className="text-sm font-medium text-foreground">{t('settings.theme_label')}</label>
                                <p className="text-xs text-muted-foreground mt-1 max-w-sm">{t('settings.theme_desc')}</p>
                            </div>
                            <div className="flex items-center gap-2 bg-muted p-1 rounded-lg border border-border">
                                <button
                                    onClick={() => setTheme('light')}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${theme === 'light' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                >
                                    {t('settings.theme_light')}
                                </button>
                                <button
                                    onClick={() => setTheme('dark')}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${theme === 'dark' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                >
                                    {t('settings.theme_dark')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
