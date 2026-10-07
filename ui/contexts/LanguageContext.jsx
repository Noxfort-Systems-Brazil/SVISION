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
 * File: LanguageContext.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: React Context provider managing internationalization (i18n), translations, and locale switching.
 */

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import ptBR from '../locales/pt_br.json';
import enUS from '../locales/en_us.json';

const dictionaries = {
    'pt_br': ptBR,
    'en_us': enUS
};

const LanguageContext = createContext();

/**
 * Formats a raw key segment into a human-readable label.
 * e.g. "cam_name_ph" → "Cam Name Ph"
 */
function humanizeKey(key) {
    return key
        .split(/[._-]/)
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

export function LanguageProvider({ children }) {
    // Default to portuguese, or read from localStorage if you wanted persistence
    const [language, setLanguage] = useState('pt_br');

    // Deduplicate missing key warnings to avoid console spam
    const warnedKeys = useRef(new Set());

    // Robust dot-notation key resolver with cascading fallback:
    // 1. Try current language dictionary
    // 2. Try English (en_us) as fallback
    // 3. Humanize the last key segment as last resort
    const t = useCallback((path) => {
        const keys = path.split('.');

        // Stage 1: Try current language
        let current = dictionaries[language];
        let found = true;
        for (const key of keys) {
            if (current === undefined || current === null || current[key] === undefined) {
                found = false;
                break;
            }
            current = current[key];
        }
        if (found) return current;

        // Stage 2: Try English fallback (if not already English)
        if (language !== 'en_us') {
            current = dictionaries['en_us'];
            found = true;
            for (const key of keys) {
                if (current === undefined || current === null || current[key] === undefined) {
                    found = false;
                    break;
                }
                current = current[key];
            }
            if (found) return current;
        }

        // Stage 3: Humanize the last key segment as graceful fallback
        if (!warnedKeys.current.has(path)) {
            warnedKeys.current.add(path);
            console.warn(`[i18n] Missing translation key: "${path}"`);
        }

        // Take the last segment and make it human-readable
        const lastKey = keys[keys.length - 1];
        return humanizeKey(lastKey);
    }, [language]);

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

// Hook to be used inside components
export function useTranslation() {
    return useContext(LanguageContext);
}
