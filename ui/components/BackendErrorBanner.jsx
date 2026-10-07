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
 * File: BackendErrorBanner.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Prominent notification banner displayed when the Python AI backend
 * fails to spawn or crashes unexpectedly, preventing a silent blank GUI.
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, XCircle, Terminal } from 'lucide-react';
import { ipcClient } from '../services/ipc_client';

export function BackendErrorBanner() {
    const [backendError, setBackendError] = useState(ipcClient.backendError);
    const [isDismissed, setIsDismissed] = useState(false);

    useEffect(() => {
        const unsubscribe = ipcClient.subscribe('backend_error', (err) => {
            setBackendError(err);
            setIsDismissed(false);
        });
        return unsubscribe;
    }, []);

    if (!backendError || isDismissed) {
        return null;
    }

    const errorMsg = backendError.error || 'Falha crítica ao iniciar o subsistema Python do SVision.';
    const pythonBin = backendError.python_bin || 'python3';
    const rootDir = backendError.root || '.';

    return (
        <div className="mx-6 mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-500 shadow-sm animate-in fade-in duration-200">
            <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold tracking-tight text-red-400">
                            Falha no Backend Python (Core AI Offline)
                        </h4>
                        <button
                            onClick={() => setIsDismissed(true)}
                            className="text-muted-foreground hover:text-foreground text-xs p-1 rounded transition-colors"
                            title="Fechar aviso"
                        >
                            <XCircle className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="text-xs text-red-300/90 leading-relaxed font-mono break-all">
                        {errorMsg}
                    </p>
                    <div className="flex items-center gap-2 pt-1 text-[11px] text-muted-foreground font-mono">
                        <Terminal className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        <span>Interpretador: {pythonBin}</span>
                        <span>•</span>
                        <span className="truncate">Raiz: {rootDir}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
