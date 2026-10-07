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
 * File: useCameraOperations.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Custom hook encapsulating camera mutations via IPC and domain validation (DIP & SRP).
 */

import { useCallback } from 'react';
import { ipcClient } from '../services/ipc_client';
import { generateDefaultCameraParams } from '../constants/cameraConfig';

export function useCameraOperations(cameras = []) {
    /**
     * Adds a camera entity after validating address uniqueness.
     * @returns {{ success: boolean, error?: string, camera?: object }}
     */
    const addCamera = useCallback(({ name, address, sensorId, synapsePort }) => {
        const trimmedName = (name || '').trim();
        const trimmedAddress = (address || '').trim();

        if (!trimmedName || !trimmedAddress) {
            return { success: false, error: 'empty_fields' };
        }

        const isDuplicate = cameras.some(c => c.address === trimmedAddress);
        if (isDuplicate) {
            return { success: false, error: 'address_exists' };
        }

        const generatedSensorId = sensorId?.trim() || trimmedName.toLowerCase().replace(/\s+/g, '_');
        const portNumber = synapsePort ? parseInt(synapsePort, 10) : 0;

        const newCam = {
            id: `manual_cam_${Date.now()}`,
            name: trimmedName,
            address: trimmedAddress,
            sensor_id: generatedSensorId,
            synapse_port: portNumber,
            status: 'online',
            scs: 100,
            fps: 12,
            parameters: generateDefaultCameraParams()
        };

        ipcClient.addCamera(newCam);
        return { success: true, camera: newCam };
    }, [cameras]);

    /**
     * Removes a camera by its ID.
     */
    const removeCamera = useCallback((cameraId) => {
        if (!cameraId) return;
        ipcClient.removeCamera(cameraId);
    }, []);

    /**
     * Replaces the camera collection in batch (e.g. via CSV import).
     */
    const importCameras = useCallback((camerasList) => {
        if (!camerasList || camerasList.length === 0) return;
        ipcClient.setCameras(camerasList);
    }, []);

    return {
        addCamera,
        removeCamera,
        importCameras
    };
}
