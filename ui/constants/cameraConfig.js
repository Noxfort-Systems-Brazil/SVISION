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
 * File: cameraConfig.js
 * Author: Gabriel Moraes
 * Date: 2026-03-27
 *
 * Description: Configs and constants for camera domain.
 */

export const YOLO_GEAR_DESCRIPTIONS = {
    'Nano': 'Baixa carga — via tranquila',
    'Small': 'Moderada — fluxo leve',
    'Medium': 'Intensa — alta densidade',
    'Heavy': 'Máxima — oclusão severa'
};

export const DEFAULT_GEAR_DESCRIPTION = 'Modelo ativo';

export const PARAM_STATUS_THEME = {
    Active: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    Settled: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20',
    Default: 'bg-secondary text-secondary-foreground border-border'
};

export function generateDefaultCameraParams() {
    return [
        { name: "Bounding Box Regressors", status: "In Process", target: "18", reviewer: "Autonomous" },
        { name: "Intersection Polygons", status: "Settled", target: "22", reviewer: "Manual / Edge" },
        { name: "Optical Flow Tracking", status: "Active", target: "45", reviewer: "Global Policy" }
    ];
}
