# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# File: scs_orchestrator.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Staggered Calibration Sequencer controlling power spikes and active limits.
"""

import asyncio
import logging
from typing import List

from src.vision.asc_analyzer import asc_analyzer

logger = logging.getLogger("scs_orchestrator")


class StaggeredCalibrationSequencer:
    """
    SCS Orchestrator.
    Prevents instantaneous system overload when the Core Server boots.
    Forces cameras to wake up in structured batches, validating ASC stability sequentially.
    """
    def __init__(self, batch_size: int = 4):
        self.batch_size = batch_size
        self.hibernating_cameras: List[str] = []
        self._orchestrator_running = False
        
    def enqueue_cold_start(self, camera_id: str):
        """Adds a camera to the hibernation queue waiting for safe startup."""
        if camera_id not in self.hibernating_cameras:
            self.hibernating_cameras.append(camera_id)
            logger.info(f"Camera {camera_id} queued for Staggered Cold Start.")

    async def run_sequence(self):
        """
        The persistent engine loop evaluating power envelopes and waking batches (FIFO order).
        """
        self._orchestrator_running = True
        logger.info(f"SCS Orchestrator online. Batch envelope: {self.batch_size} streams.")
        
        while self._orchestrator_running:
            if not self.hibernating_cameras:
                await asyncio.sleep(2.0)
                continue
                
            # If ASC is currently busy calibrating the maximum envelope, yield.
            if len(asc_analyzer.calibrating_cameras) >= self.batch_size:
                await asyncio.sleep(1.0)
                continue
            
            # Wake up next camera in FIFO order
            next_cam = self.hibernating_cameras.pop(0)
            
            # Fire and forget the ASC convergence in the background
            asyncio.create_task(asc_analyzer.start_calibration(next_cam))
            
            # Graceful interval between successive GPU model loads
            await asyncio.sleep(0.5)


scs_orchestrator = StaggeredCalibrationSequencer()
