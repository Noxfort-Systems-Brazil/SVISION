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
 * File: AddCameraModal.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Modal dialog for manually registering a new camera sensor.
 */

import React, { useState } from 'react';
import { Modal } from '../Modal';
import { useTranslation } from '../../contexts/LanguageContext';

export function AddCameraModal({ isOpen, onClose, onAddCamera }) {
    const { t } = useTranslation();
    const [formName, setFormName] = useState('');
    const [formAddress, setFormAddress] = useState('');
    const [formSensorId, setFormSensorId] = useState('');
    const [formSynapsePort, setFormSynapsePort] = useState('');
    const [validationError, setValidationError] = useState('');

    const resetForm = () => {
        setFormName('');
        setFormAddress('');
        setFormSensorId('');
        setFormSynapsePort('');
        setValidationError('');
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmedName = formName.trim();
        const trimmedAddr = formAddress.trim();
        if (!trimmedName || !trimmedAddr) {
            setValidationError('Preencha o nome e o endereço da câmera.');
            return;
        }

        const isValidScheme = /^(rtsp|rtsps|http|https):\/\/.+/i.test(trimmedAddr) || /^(\/dev\/|\d+$|.+\.(mp4|mkv|avi)$)/i.test(trimmedAddr);
        if (!isValidScheme) {
            setValidationError('Endereço inválido. Use rtsp://, http://, /dev/video* ou índice de dispositivo.');
            return;
        }

        if (formSynapsePort) {
            const p = parseInt(formSynapsePort, 10);
            if (Number.isNaN(p) || p < 1024 || p > 65535) {
                setValidationError('A porta TCP Synapse deve estar entre 1024 e 65535 (ou vazio para automática).');
                return;
            }
        }

        setValidationError('');
        const result = onAddCamera({
            name: trimmedName,
            address: trimmedAddr,
            sensorId: formSensorId,
            synapsePort: formSynapsePort
        });

        if (result?.success) {
            resetForm();
            onClose();
        } else if (result?.error === 'address_exists') {
            setValidationError(t('address_exists') || "Já existe uma câmera configurada com este endereço.");
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={handleClose}
            title={t('sensors.add_title')}
            subtitle={t('sensors.add_subtitle')}
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                {validationError && (
                    <div className="text-xs text-red-500 bg-red-500/10 border border-red-500/30 rounded-md px-3 py-2">
                        {validationError}
                    </div>
                )}
                <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">{t('app_name')} - Camera Name</label>
                    <input
                        type="text"
                        required
                        autoFocus
                        placeholder={t('sensors.cam_name_ph')}
                        value={formName}
                        onChange={(e) => setFormName(e.target.value)}
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-all"
                    />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">{t('sensors.address')} (RTSP/HTTP)</label>
                    <input
                        type="text"
                        required
                        placeholder={t('sensors.cam_addr_ph')}
                        value={formAddress}
                        onChange={(e) => setFormAddress(e.target.value)}
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-all"
                    />
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground flex items-center justify-between">
                        <span>ID do Sensor (Synapse)</span>
                        <span className="text-xs text-muted-foreground font-normal">Identificador único</span>
                    </label>
                    <input
                        type="text"
                        placeholder="Ex: cruzamento_paulista_01 (Padrão: nome da câmera)"
                        value={formSensorId}
                        onChange={(e) => setFormSensorId(e.target.value)}
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-all"
                    />
                    <p className="text-[11px] text-muted-foreground">Nome de identificação do ponto de monitoramento enviado nos pacotes TCP para a central Synapse.</p>
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground flex items-center justify-between">
                        <span>Porta TCP Synapse</span>
                        <span className="text-xs text-muted-foreground font-normal">Opcional</span>
                    </label>
                    <input
                        type="number"
                        placeholder="Ex: 9001 (Automático se vazio)"
                        value={formSynapsePort}
                        onChange={(e) => setFormSynapsePort(e.target.value)}
                        className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-all"
                    />
                </div>
                <div className="pt-4 flex items-center justify-end gap-2 border-t border-border mt-4">
                    <button
                        type="button"
                        onClick={handleClose}
                        className="px-4 py-2 bg-muted text-muted-foreground hover:bg-accent rounded-md text-sm font-medium transition-colors"
                    >
                        {t('sensors.cancel_btn')}
                    </button>
                    <button
                        type="submit"
                        className="px-4 py-2 bg-primary text-primary-foreground hover:opacity-90 rounded-md text-sm font-medium shadow-sm transition-opacity"
                    >
                        {t('sensors.save_btn')}
                    </button>
                </div>
            </form>
        </Modal>
    );
}
