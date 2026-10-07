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
 * File: CamerasTab.jsx
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Orchestrator view for camera sensors management and inspection.
 */

import React, { useState, useRef } from 'react';
import { useCameras } from '../hooks/useCameras';
import { useCameraOperations } from '../hooks/useCameraOperations';
import { exportCamerasToCsv, parseCamerasFromCsv, readCsvFile } from '../services/cameraCsvService';
import { CameraList } from '../components/CameraList';
import { CameraDetailPane } from '../components/cameras/CameraDetailPane';
import { AddCameraModal } from '../components/cameras/AddCameraModal';
import { useTranslation } from '../contexts/LanguageContext';
import { Upload, Download, Plus } from 'lucide-react';

export function CamerasTab() {
    const cameras = useCameras();
    const { addCamera, removeCamera, importCameras } = useCameraOperations(cameras);
    const [selectedId, setSelectedId] = useState(null);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const fileInputRef = useRef(null);
    const { t } = useTranslation();

    const selectedCam = cameras.find(c => c.id === selectedId);

    const handleExport = () => {
        exportCamerasToCsv(cameras);
    };

    const triggerImport = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleImport = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const text = await readCsvFile(file);
            const parsedCameras = parseCamerasFromCsv(text);
            if (parsedCameras.length > 0) {
                importCameras(parsedCameras);
                setSelectedId(null);
            }
        } finally {
            e.target.value = null;
        }
    };

    const handleAddCamera = (formData) => {
        const result = addCamera(formData);
        if (result.success && result.camera) {
            setSelectedId(result.camera.id);
        }
        return result;
    };

    const handleRemoveCamera = (cameraId) => {
        removeCamera(cameraId);
        setSelectedId(null);
    };

    return (
        <div className="h-full flex gap-4">
            <input
                type="file"
                accept=".csv"
                ref={fileInputRef}
                className="hidden"
                onChange={handleImport}
            />

            {/* Left Pane: List and Actions */}
            <div className="w-[300px] shrink-0 bg-card border border-border rounded-xl flex flex-col">
                <div className="p-3 border-b border-border flex flex-col gap-2 bg-muted/40 rounded-t-xl shrink-0">
                    <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="w-full flex items-center justify-center gap-2 bg-primary hover:opacity-90 text-primary-foreground px-3 py-2 rounded-md text-sm font-semibold transition-colors"
                    >
                        <Plus className="w-4 h-4" /> {t('sensors.add_cam')}
                    </button>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={triggerImport}
                            className="flex-1 flex items-center justify-center gap-2 border border-border bg-background hover:bg-accent text-foreground px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
                        >
                            <Upload className="w-3.5 h-3.5" /> {t('sensors.import_csv')}
                        </button>
                        <button
                            onClick={handleExport}
                            className="flex-1 flex items-center justify-center gap-2 border border-border bg-background hover:bg-accent text-foreground px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
                        >
                            <Download className="w-3.5 h-3.5" /> {t('sensors.export_csv')}
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-hidden">
                    <CameraList
                        cameras={cameras}
                        selectedId={selectedId}
                        onSelect={setSelectedId}
                    />
                </div>
            </div>

            {/* Right Pane: Detail Inspector */}
            <CameraDetailPane
                camera={selectedCam}
                onRemove={handleRemoveCamera}
            />

            {/* Add Camera Modal Dialog */}
            <AddCameraModal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                onAddCamera={handleAddCamera}
            />
        </div>
    );
}
