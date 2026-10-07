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
 * File: SynapseTelemetryGrid.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Visualizes real-time traffic dynamics and edge sensor telemetry from Synapse.
 */

import React from 'react';

export function SynapseTelemetryGrid({ camera }) {
    const synapse = camera?.synapse;
    const trafficDynamics = synapse?.traffic || synapse?.fluid_dynamics || {};
    const entries = Object.entries(trafficDynamics);
    const hasData = Boolean(synapse && entries.length > 0);

    return (
        <div className="mt-6 border border-border rounded-xl p-5 bg-background">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-md font-semibold text-card-foreground flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${synapse ? 'bg-indigo-500 animate-pulse' : 'bg-muted-foreground'}`}></div>
                    Telemetria em Tempo Real (Synapse)
                </h3>
                {synapse && (
                    <div className="text-xs text-muted-foreground font-mono flex gap-3">
                        <span>Sensor: {synapse.sensor_id || camera.sensor_id || camera.id}</span>
                        <span>Janela: {synapse.window_ms || 1000}ms</span>
                        <span>T: {synapse.timestamp}</span>
                    </div>
                )}
            </div>

            {!hasData ? (
                <div className="text-sm text-muted-foreground py-4 text-center border border-dashed border-border rounded-lg bg-muted/10">
                    Aguardando telemetria em tempo real da GPU (12 FPS)...
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {entries.map(([approach, data]) => {
                        const count = data.count ?? data.queue ?? 0;
                        const speed = data.speed_kmh ?? data.speed ?? 0;
                        const occupancy = data.occupancy ?? 0;
                        const density = data.density ?? 0;
                        const isActive = count > 0 || speed > 0 || occupancy > 0 || density > 0;

                        return (
                            <div key={approach} className="bg-muted/30 border border-border rounded-lg p-3 flex flex-col gap-3">
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground border-b border-border pb-2">
                                    {approach.replace('approach_', 'Via ')}
                                </div>
                                {!isActive ? (
                                    <div className="text-xs text-center text-muted-foreground py-2 italic opacity-60">
                                        Nenhum fluxo transitando
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-2 text-sm">
                                        <div className="flex justify-between items-center border-b border-border/50 pb-1">
                                            <span className="text-muted-foreground text-xs">Contagem (veh):</span>
                                            <span className="font-mono text-foreground font-semibold">{count}</span>
                                        </div>
                                        <div className="flex justify-between items-center border-b border-border/50 pb-1">
                                            <span className="text-muted-foreground text-xs">Velocidade:</span>
                                            <span className="font-mono text-foreground">{Number(speed).toFixed(1)} km/h</span>
                                        </div>
                                        <div className="flex justify-between items-center border-b border-border/50 pb-1">
                                            <span className="text-muted-foreground text-xs">Ocupação:</span>
                                            <span className="font-mono text-foreground">{(Number(occupancy) * 100).toFixed(0)}%</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-muted-foreground text-xs">Densidade:</span>
                                            <span className="font-mono text-foreground">{Number(density).toFixed(1)}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
