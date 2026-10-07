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
 * File: cameraCsvService.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Dedicated service for importing and exporting camera CSV payloads (SRP).
 */

import { generateDefaultCameraParams } from '../constants/cameraConfig';

/**
 * Serializes camera list to CSV string and triggers browser file download.
 * @param {Array} cameras 
 */
export function exportCamerasToCsv(cameras) {
    if (!cameras || cameras.length === 0) return;

    let csvContent = "NomeDaCamera,EnderecoReconhecimento\n";

    cameras.forEach(cam => {
        const rawName = cam.name || '';
        const rawAddr = cam.address || 'rtsp://unknown/stream';
        const safeName = rawName.includes(',') ? `"${rawName}"` : rawName;
        const safeAddr = rawAddr.includes(',') ? `"${rawAddr}"` : rawAddr;
        csvContent += `${safeName},${safeAddr}\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `svision_sensors_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Parses CSV raw text into normalized camera entities.
 * @param {string} text 
 * @returns {Array} Array of camera objects
 */
export function parseCamerasFromCsv(text) {
    if (!text) return [];

    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length === 0) return [];

    let startIndex = 0;
    if (lines[0].toLowerCase().includes('nome')) {
        startIndex = 1;
    }

    const cameras = [];
    const timestamp = Date.now();

    for (let i = startIndex; i < lines.length; i++) {
        const columns = lines[i].split(',');
        if (columns.length >= 2) {
            const name = columns[0].replace(/"/g, '').trim();
            const address = columns[1].replace(/"/g, '').trim();

            cameras.push({
                id: `imported_cam_${i}_${timestamp}`,
                name,
                address,
                status: 'online',
                scs: 100,
                fps: 30,
                parameters: generateDefaultCameraParams()
            });
        }
    }

    return cameras;
}

/**
 * Reads a File instance as text asynchronously.
 * @param {File} file 
 * @returns {Promise<string>}
 */
export function readCsvFile(file) {
    return new Promise((resolve, reject) => {
        if (!file) {
            resolve('');
            return;
        }
        const reader = new FileReader();
        reader.onload = (event) => resolve(event.target.result || '');
        reader.onerror = (err) => reject(err);
        reader.readAsText(file);
    });
}
