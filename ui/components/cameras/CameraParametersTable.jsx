/*
 * SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
 * Copyright (C) 2026 Noxfort Systems
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * SPDX-FileCopyrightText: 2026 Noxfort Systems
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
 * File: CameraParametersTable.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Table component displaying active neural/vision parameters and review status.
 */

import React from 'react';
import { useTranslation } from '../../contexts/LanguageContext';
import { PARAM_STATUS_THEME } from '../../constants/cameraConfig';

export function CameraParametersTable({ parameters = [], tuningParams = null, calibrated = false }) {
    const { t } = useTranslation();

    const getStatusStyle = (status) => {
        return PARAM_STATUS_THEME[status] || PARAM_STATUS_THEME.Default;
    };

    const effectiveParams = tuningParams && Object.keys(tuningParams).length > 0
        ? [
            {
                name: 'Confidence Threshold',
                status: 'Active',
                target: String(tuningParams.confidence_threshold ?? 0.35),
                reviewer: 'Backend Runtime',
            },
            {
                name: 'NMS Threshold',
                status: 'Active',
                target: String(tuningParams.nms_threshold ?? 0.45),
                reviewer: 'Backend Runtime',
            },
            {
                name: 'Homography Calibration',
                status: calibrated ? 'Settled' : 'In Process',
                target: calibrated ? '3x3 Matrix' : 'Uncalibrated',
                reviewer: calibrated ? 'Operator / Edge' : 'Pending',
            },
            {
                name: 'Node Approach / Direction',
                status: 'Settled',
                target: `${tuningParams.approach || 'node'} (${tuningParams.nominal_direction ?? 0}°)`,
                reviewer: 'Edge Policy',
            },
        ]
        : parameters;

    return (
        <div className="border border-border rounded-xl mt-6 overflow-hidden">
            <table className="w-full text-sm text-left">
                <thead className="bg-muted text-muted-foreground text-xs uppercase font-medium border-b border-border">
                    <tr>
                        <th className="px-4 py-3">{t('sensors.table_param')}</th>
                        <th className="px-4 py-3">{t('sensors.table_status')}</th>
                        <th className="px-4 py-3">{t('sensors.table_target')}</th>
                        <th className="px-4 py-3 text-right">{t('sensors.table_reviewer')}</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border text-foreground">
                    {effectiveParams && effectiveParams.map((param, idx) => (
                        <tr key={idx} className="hover:bg-accent/50 transition-colors">
                            <td className="px-4 py-3 font-medium text-card-foreground">{param.name}</td>
                            <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded text-xs border inline-block ${getStatusStyle(param.status)}`}>
                                    {param.status}
                                </span>
                            </td>
                            <td className="px-4 py-3">{param.target}</td>
                            <td className="px-4 py-3 text-right text-muted-foreground">{param.reviewer}</td>
                        </tr>
                    ))}

                    {(!effectiveParams || effectiveParams.length === 0) && (
                        <tr>
                            <td colSpan="4" className="px-4 py-6 text-center text-muted-foreground">
                                {t('sensors.no_params')}
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
