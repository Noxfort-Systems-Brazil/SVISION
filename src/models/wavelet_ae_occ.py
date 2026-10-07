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

# File: wavelet_ae_occ.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Wavelet AutoEncoder for One-Class Classification (OCC) Anomaly Detection.
Decomposes incoming traffic tensors into spatial sub-bands to detect occlusion and accidents.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class WaveletAEOCC(nn.Module):
    """
    Wavelet AutoEncoder for One-Class Classification (Anomaly Detection).
    Operates by decomposing incoming traffic tensors into spatial sub-bands (resembling DWT).
    Trained strictly on 'Normal' driving. When an adversarial attack, severe accident, 
    or camera occlusion happens, the model fails to reconstruct it, creating a huge MSE spike.
    """
    def __init__(self, in_channels=3):
        super().__init__()
        
        # Encoder (Simulated Wavelet DWT Sub-band Decomposition)
        self.enc_conv1 = nn.Conv2d(in_channels, 16, kernel_size=4, stride=2, padding=1)
        self.enc_conv2 = nn.Conv2d(16, 32, kernel_size=4, stride=2, padding=1)
        self.enc_conv3 = nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1)
        
        # Decoder (Simulated Inverse DWT Reconstruction)
        self.dec_conv1 = nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1)
        self.dec_conv2 = nn.ConvTranspose2d(32, 16, kernel_size=4, stride=2, padding=1)
        self.dec_conv3 = nn.ConvTranspose2d(16, in_channels, kernel_size=4, stride=2, padding=1)

    def forward(self, x):
        # Decomposition Phase (Isolating intrinsic semantic frequencies)
        e1 = F.leaky_relu(self.enc_conv1(x), 0.2)
        e2 = F.leaky_relu(self.enc_conv2(e1), 0.2)
        latent_manifold = F.leaky_relu(self.enc_conv3(e2), 0.2)
        
        # Reconstruction Phase (Attempting to restore normal physics)
        d1 = F.leaky_relu(self.dec_conv1(latent_manifold), 0.2)
        d2 = F.leaky_relu(self.dec_conv2(d1), 0.2)
        
        # Sigmoid collapses pixels back to strict 0.0-1.0 radiometric ranges
        out = torch.sigmoid(self.dec_conv3(d2))
        return out
