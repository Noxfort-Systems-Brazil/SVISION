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
 * File: MetricDetailModal.jsx
 * Author: Gabriel Moraes
 * Date: 2026-09-05
 *
 * Description: Dedicated inspection modal for deep telemetry metrics and operation traces.
 */

import React, { useMemo } from 'react';
import { Info } from 'lucide-react';
import { Modal } from '../Modal';
import { useTranslation } from '../../contexts/LanguageContext';

/**
 * Inspection modal displaying deep details for the selected metric or operation.
 *
 * @param {Object} props
 * @param {Object|null} props.metric - Currently selected metric or null
 * @param {string} props.metric.title - Metric title
 * @param {string} props.metric.value - Formatted value
 * @param {string} props.metric.desc - Detailed description
 * @param {Function} props.onClose - Modal close handler
 */
export function MetricDetailModal({ metric, onClose }) {
    const { t } = useTranslation();

    // Stable simulated memory pointer while this metric is open
    const signalIntercept = useMemo(() => {
        if (!metric) return '';
        return `0x${Math.floor(Math.random() * 99999).toString(16)}`;
    }, [metric]);

    return (
        <Modal
            isOpen={Boolean(metric)}
            onClose={onClose}
            title={metric?.title}
            subtitle={t('modals.deep_view')}
        >
            <div className="flex flex-col items-center justify-center p-8 bg-muted/20 border border-border rounded-lg border-dashed">
                <Info className="w-8 h-8 text-muted-foreground mb-4" />
                <div className="text-3xl font-bold text-foreground mb-2">{metric?.value}</div>
                <p className="text-sm text-muted-foreground text-center max-w-sm leading-relaxed">{metric?.desc}</p>
                <div className="w-full mt-6 space-y-2">
                    <div className="flex justify-between text-xs text-muted-foreground border-b border-border pb-2">
                        <span>{t('modals.sig_intercept')}</span>
                        <span className="font-mono text-muted-foreground">{signalIntercept}</span>
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground border-b border-border pb-2">
                        <span>{t('modals.orig_proc')}</span>
                        <span className="font-mono text-muted-foreground">core_engine.py</span>
                    </div>
                </div>
            </div>
        </Modal>
    );
}
