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
 * File: SynapseTab.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Network egress and Synapse telemetry dashboard monitoring port bindings, latency, and socket status.
 */
import React, { useState } from 'react';
import { EChart } from '../components/EChart';
import { MetricCard } from '../components/MetricCard';
import { useNetworkLatency } from '../hooks/useNetworkLatency';
import { useNetworkStats } from '../hooks/useNetworkStats';
import { useCameras } from '../hooks/useCameras';
import { ipcClient } from '../services/ipc_client';
import { useTranslation } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { Network, DatabaseZap, ServerOff, Radio, Server, CheckCircle2 } from 'lucide-react';
import { Modal } from '../components/Modal';

export function SynapseTab() {
    const latencyHistory = useNetworkLatency();
    const netStats = useNetworkStats();
    const cameras = useCameras();
    const { t } = useTranslation();
    const { theme } = useTheme();

    const [hostInput, setHostInput] = useState('127.0.0.1');
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    const handleSaveHost = (e) => {
        e.preventDefault();
        if (!hostInput.trim()) return;
        setIsSaving(true);
        ipcClient.updateSynapseConfig({ host: hostInput.trim() });
        setTimeout(() => {
            setIsSaving(false);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 2500);
        }, 400);
    };

    // Interactivity State
    const [selectedMetric, setSelectedMetric] = useState(null);

    // Extract timeseries for ECharts
    const dataPoints = latencyHistory.map(pt => pt.latency_ms);

    // Clean, minimalist ECharts configuration avoiding heavy effects
    // Canvas API cannot natively parse var(--color) in addColorStop, so we use explicit hex colors.
    const primaryColor = theme === 'dark' ? '#fafafa' : '#18181b';
    const cardBg = theme === 'dark' ? '#09090b' : '#ffffff';
    const borderColor = theme === 'dark' ? '#27272a' : '#e4e4e7';
    const cardFg = theme === 'dark' ? '#fafafa' : '#09090b';
    const mutedFg = theme === 'dark' ? '#a1a1aa' : '#71717a';

    const getChartOptions = () => ({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: cardBg,
            borderColor: borderColor,
            textStyle: { color: cardFg }
        },
        grid: { left: '1%', right: '1%', bottom: '0%', top: '5%', containLabel: true },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: latencyHistory.map(pt => new Date(pt.timestamp).toLocaleTimeString()),
            axisLine: { lineStyle: { color: borderColor } },
            axisTick: { show: false },
            axisLabel: { color: mutedFg, fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            splitLine: { lineStyle: { color: borderColor, type: 'dashed' } },
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: mutedFg, fontSize: 10, align: 'right' }
        },
        series: [
            {
                name: 'Latency (ms)',
                type: 'line',
                smooth: true,
                symbol: 'none',
                lineStyle: { width: 2, color: primaryColor },
                areaStyle: {
                    color: {
                        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: primaryColor },
                            { offset: 1, color: 'transparent' }
                        ]
                    }
                },
                data: dataPoints
            }
        ]
    });

    return (
        <div className="h-full flex flex-col space-y-4">
            {/* Top Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
                <MetricCard
                    title={t('network.active_conn')}
                    value={netStats.active_connections.toLocaleString()}
                    trend={netStats.conn_trend}
                    desc={t('network.from_yesterday')}
                    onClick={() => setSelectedMetric({ title: t('network.active_conn'), value: netStats.active_connections.toLocaleString(), desc: t('network.active_conn_desc') })}
                />
                <MetricCard
                    title={t('network.avg_latency')}
                    value={`${dataPoints.length > 0 ? dataPoints[dataPoints.length - 1] : 0} ms`}
                    trend="-2ms"
                    desc={t('network.from_yesterday')}
                    onClick={() => setSelectedMetric({ title: t('network.avg_latency'), value: `${dataPoints.length > 0 ? dataPoints[dataPoints.length - 1] : 0} ms`, desc: t('network.avg_latency_desc') })}
                />
                <MetricCard
                    title={t('network.packet_del')}
                    value={`${netStats.packet_delivery}%`}
                    trend={netStats.delivery_trend}
                    desc={t('network.from_yesterday')}
                    onClick={() => setSelectedMetric({ title: t('network.packet_del'), value: `${netStats.packet_delivery}%`, desc: t('network.packet_del_desc') })}
                />
                <MetricCard
                    title={t('network.bw_peak')}
                    value={`${netStats.bandwidth_peak} MB/s`}
                    trend={netStats.bandwidth_trend}
                    desc={t('network.from_yesterday')}
                    onClick={() => setSelectedMetric({ title: t('network.bw_peak'), value: `${netStats.bandwidth_peak} MB/s`, desc: t('network.bw_peak_desc') })}
                />
            </div>

            {/* Core Network Graph */}
            <div className="flex-1 bg-card border border-border rounded-xl p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-2">
                    <div>
                        <h3 className="text-base font-semibold text-card-foreground flex items-center gap-2">
                            <Network className="w-5 h-5 text-muted-foreground" />
                            {t('network.reliability')}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">{t('network.reliability_desc')}</p>
                    </div>
                    {/* Status Pip */}
                    <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{t('status_online')}</span>
                    </div>
                </div>

                <div className="flex-1 w-full relative min-h-[250px] mt-4 opacity-80 mix-blend-screen">
                    <EChart
                        option={getChartOptions()}
                        style={{ height: '100%', width: '100%', position: 'absolute' }}
                    />
                </div>
            </div>

            {/* Synapse TCP Ports Gatekeeper Section */}
            <div className="bg-card border border-border rounded-xl p-6 flex flex-col gap-4">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-border">
                    <div>
                        <h3 className="text-base font-semibold text-card-foreground flex items-center gap-2">
                            <Radio className="w-5 h-5 text-indigo-400" />
                            Porteiro de Rede em Tempo Real (<span className="font-mono text-xs text-indigo-400">svision-go</span>)
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                            Portas TCP dedicadas por câmera para PUSH contínuo ao servidor central do Synapse.
                        </p>
                    </div>
                    {/* Host Configuration Form */}
                    <form onSubmit={handleSaveHost} className="flex items-center gap-2">
                        <div className="flex items-center gap-2 bg-muted/30 border border-border rounded-lg px-3 py-1.5">
                            <Server className="w-4 h-4 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground whitespace-nowrap">IP Synapse:</span>
                            <input
                                type="text"
                                value={hostInput}
                                onChange={(e) => setHostInput(e.target.value)}
                                placeholder="127.0.0.1"
                                className="bg-transparent text-xs font-mono text-foreground focus:outline-none w-32"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={isSaving}
                            className="px-3 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:opacity-90 transition-opacity flex items-center gap-1.5"
                        >
                            {saveSuccess ? (
                                <>
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />
                                    <span>Salvo</span>
                                </>
                            ) : (
                                <span>Salvar IP</span>
                            )}
                        </button>
                    </form>
                </div>

                {/* Ports Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-border text-muted-foreground">
                                <th className="pb-2 font-medium">Câmera</th>
                                <th className="pb-2 font-medium">Sensor ID (Synapse)</th>
                                <th className="pb-2 font-medium">Porta TCP</th>
                                <th className="pb-2 font-medium">Destino</th>
                                <th className="pb-2 font-medium text-right">Status do Stream</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border/40">
                            {cameras.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="py-6 text-center text-muted-foreground">
                                        Nenhuma câmera conectada ao despachante no momento.
                                    </td>
                                </tr>
                            ) : (
                                cameras.map((cam) => {
                                    const port = cam.synapse_port || 9001;
                                    const isConnected = cam.synapse_status === 'CONNECTED';
                                    return (
                                        <tr key={cam.id} className="hover:bg-muted/20 transition-colors">
                                            <td className="py-3 font-medium text-foreground">{cam.name}</td>
                                            <td className="py-3 font-mono text-muted-foreground">{cam.sensor_id || cam.id}</td>
                                            <td className="py-3 font-mono text-indigo-400 font-semibold">{port}</td>
                                            <td className="py-3 font-mono text-muted-foreground">{hostInput}:{port}</td>
                                            <td className="py-3 text-right">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border ${
                                                    isConnected
                                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                                                        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                                                }`}>
                                                    <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
                                                    {cam.synapse_status || 'READY'}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <Modal
                isOpen={!!selectedMetric}
                onClose={() => setSelectedMetric(null)}
                title={selectedMetric?.title}
                subtitle={t('modals.syn_diag')}
            >
                <div className="p-6 bg-muted/20 border border-border rounded-lg text-center">
                    <DatabaseZap className="w-10 h-10 text-muted-foreground mx-auto mb-4" />
                    <h2 className="text-3xl font-bold text-foreground mb-2">{selectedMetric?.value}</h2>
                    <p className="text-sm text-muted-foreground">{selectedMetric?.desc}</p>
                </div>
            </Modal>
        </div>
    );
}
