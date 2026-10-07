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
 * File: CameraDetailPane.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Detailed inspector pane for the selected camera sensor (SRP & ISP).
 */

import React from 'react';
import { BrainCircuit, Expand, Trash2 } from 'lucide-react';
import { useTranslation } from '../../contexts/LanguageContext';
import { MetricCard } from '../MetricCard';
import { SynapseTelemetryGrid } from './SynapseTelemetryGrid';
import { CameraParametersTable } from './CameraParametersTable';
import { YOLO_GEAR_DESCRIPTIONS, DEFAULT_GEAR_DESCRIPTION } from '../../constants/cameraConfig';

export function CameraDetailPane({ camera, onRemove }) {
    const { t } = useTranslation();

    if (!camera) {
        return (
            <div className="flex-1 bg-card border border-border rounded-xl flex flex-col items-center justify-center text-muted-foreground bg-accent/20 overflow-hidden">
                <BrainCircuit className="w-10 h-10 mb-4 opacity-50" />
                <p className="text-sm font-medium">{t('sensors.select_inspect')}</p>
            </div>
        );
    }

    const gearDescription = YOLO_GEAR_DESCRIPTIONS[camera.active_gear || 'Nano'] || DEFAULT_GEAR_DESCRIPTION;
    const isConnected = camera.synapse_status === 'CONNECTED';

    return (
        <div className="flex-1 bg-card border border-border rounded-xl flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto w-full">
                {/* Header */}
                <div className="border-b border-border p-6 flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold tracking-tight text-card-foreground flex items-center gap-3">
                            {camera.name}
                        </h2>
                        <div className="flex flex-wrap items-center gap-2 mt-1.5">
                            <p className="text-sm text-muted-foreground">
                                {t('sensors.address')}: <span className="font-mono">{camera.address}</span>
                            </p>
                            <span className="text-muted-foreground opacity-40">•</span>
                            <span className="text-xs text-muted-foreground font-mono bg-muted/60 px-2 py-0.5 rounded border border-border">
                                Sensor ID: <strong className="text-foreground">{camera.sensor_id || camera.id}</strong>
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded font-mono border flex items-center gap-1.5 ${
                                isConnected
                                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                            }`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
                                Synapse PUSH: Porta {camera.synapse_port || 9001} ({camera.synapse_status || 'READY'})
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="p-2 border border-border rounded-md hover:bg-accent text-muted-foreground transition-colors" title="Expand View">
                            <Expand className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => onRemove(camera.id)}
                            className="p-2 border border-border rounded-md hover:bg-red-500/10 hover:text-red-500 text-muted-foreground transition-colors"
                            title="Deallocate Edge Sensor"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Content Body */}
                <div className="p-6 space-y-4">
                    {/* Stream Health Indicator */}
                    {camera.stream_health && (
                        <div className="flex items-center gap-4 bg-muted/30 border border-border rounded-lg px-4 py-2.5 text-xs">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${camera.stream_health.is_receiving ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                                <span className="text-muted-foreground">
                                    {camera.stream_health.is_receiving ? 'Recebendo Frames' : 'Sem Frames'}
                                </span>
                            </div>
                            <span className="text-muted-foreground font-mono">
                                Recebidos: {camera.stream_health.frames_received}
                            </span>
                            <span className="text-muted-foreground font-mono">
                                Perdidos: {camera.stream_health.dropped}
                            </span>
                        </div>
                    )}

                    {/* Main Metrics Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <MetricCard
                            title={t('sensors.scs_conf')}
                            value={`${camera.scs}%`}
                            desc={camera.scs >= 98 ? t('sensors.scs_calib') : t('sensors.scs_bg')}
                        />
                        <MetricCard
                            title={t('sensors.inf_rate')}
                            value={`${camera.fps} FPS`}
                            desc={t('sensors.inf_desc')}
                        />
                        <MetricCard
                            title="Marcha YOLO"
                            value={camera.active_gear || 'Nano'}
                            desc={gearDescription}
                        />
                    </div>

                    {/* Telemetria em Tempo Real Synapse */}
                    <SynapseTelemetryGrid camera={camera} />

                    {/* Data Table */}
                    <CameraParametersTable parameters={camera.parameters} />
                </div>
            </div>
        </div>
    );
}
