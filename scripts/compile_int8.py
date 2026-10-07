#!/usr/bin/env python3
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
#
# File: compile_int8.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
TensorRT INT8 Engine Compiler for SVision.

Compiles master PyTorch weights (.pt) from src/models/yolo/ into optimized
TensorRT INT8 binary engines (.engine) tailored specifically for the host GPU.

Usage:
  python scripts/compile_int8.py --all
  python scripts/compile_int8.py --gear Nano
  python scripts/compile_int8.py --gear Small --calib coco8.yaml
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("compile_int8")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT_DIR, "src", "models", "yolo")

GEAR_MAP = {
    "Nano": "yolo11n.pt",
    "Small": "yolo11s.pt",
    "Medium": "yolo11m.pt",
    "Heavy": "yolo11x.pt"
}


def check_cuda_environment():
    """Validates GPU availability and TensorRT readiness."""
    try:
        import torch
        if not torch.cuda.is_available():
            logger.error("No NVIDIA GPU / CUDA detected! TensorRT requires an NVIDIA GPU.")
            return False
        
        gpu_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        logger.info("=" * 60)
        logger.info(f"NVIDIA GPU Detected: {gpu_name}")
        logger.info(f"Compute Capability : {capability[0]}.{capability[1]}")
        logger.info(f"Total VRAM         : {vram_gb:.2f} GB")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"Failed checking CUDA environment: {e}")
        return False


def compile_model(gear_name: str, calib_data: str = "coco8.yaml", fp16_only: bool = False):
    """Compiles a single YOLO model to TensorRT INT8 or FP16 engine."""
    file_name = GEAR_MAP.get(gear_name)
    if not file_name:
        logger.error(f"Unknown gear '{gear_name}'. Available: {list(GEAR_MAP.keys())}")
        return False

    pt_path = os.path.join(MODELS_DIR, file_name)
    engine_path = pt_path.replace(".pt", ".engine")

    if not os.path.isfile(pt_path):
        logger.error(f"Master weights missing: {pt_path}")
        return False

    logger.info(f"\n[Compiling] Gear: {gear_name} ({file_name})")
    logger.info(f"Source: {pt_path}")
    logger.info(f"Target: {engine_path}")

    try:
        from ultralytics import YOLO
        model = YOLO(pt_path)

        if fp16_only:
            logger.info("Exporting to TensorRT FP16 (Half-Precision)...")
            model.export(
                format="engine",
                half=True,
                dynamic=True,
                workspace=4,
                verbose=False
            )
        else:
            logger.info(f"Exporting to TensorRT INT8 (Calibrating with {calib_data})...")
            try:
                model.export(
                    format="engine",
                    int8=True,
                    data=calib_data,
                    dynamic=True,
                    workspace=4,
                    verbose=False
                )
            except Exception as int8_err:
                logger.warning(f"INT8 calibration failed ({int8_err}). Falling back to FP16...")
                model.export(
                    format="engine",
                    half=True,
                    dynamic=True,
                    workspace=4,
                    verbose=False
                )

        if os.path.isfile(engine_path):
            size_mb = os.path.getsize(engine_path) / (1024 * 1024)
            logger.info(f"✔ Successfully compiled [{gear_name}]. Engine size: {size_mb:.1f} MB.")
            return True
        else:
            logger.error(f"✘ Compilation finished but {engine_path} was not found.")
            return False

    except Exception as e:
        logger.error(f"Failed to compile {gear_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SVision TensorRT INT8 Engine Compiler")
    parser.add_argument("--all", action="store_true", help="Compile all 4 YOLO gears (Nano, Small, Medium, Heavy)")
    parser.add_argument("--gear", type=str, default="Nano", help="Specific gear to compile (Nano, Small, Medium, Heavy)")
    parser.add_argument("--calib", type=str, default="coco8.yaml", help="Calibration dataset for INT8 scale factors")
    parser.add_argument("--fp16", action="store_true", help="Force FP16 export instead of INT8")
    parser.add_argument("--check", action="store_true", help="Only check CUDA environment and exit")

    args = parser.parse_args()

    if not check_cuda_environment():
        if args.check:
            sys.exit(1)
        logger.warning("Continuing without CUDA (compilation may fail if TensorRT is not configured for CPU).")

    if args.check:
        sys.exit(0)

    gears_to_compile = list(GEAR_MAP.keys()) if args.all else [args.gear]

    success_count = 0
    for gear in gears_to_compile:
        if compile_model(gear, calib_data=args.calib, fp16_only=args.fp16):
            success_count += 1

    logger.info("=" * 60)
    logger.info(f"Compilation finished. {success_count}/{len(gears_to_compile)} engines ready.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
