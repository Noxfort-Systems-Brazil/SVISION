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

# File: mock_cameras.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
High-Throughput MJPEG Mock Video Server for Pipeline Stress Testing.
Serves simulated RTSP/HTTP streams in-memory to validate multi-camera ingest performance.
"""

import sys
import os
import time
import threading
import socket
import struct
import msgpack
import cv2
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

# Gerar um único frame MJPEG em memória para poupar CPU do processo mock
# mas o suficiente para que o SVISION decodifique 900 vezes de forma intensa
dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(dummy_frame, "SVISION MOCK", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
ret, jpeg = cv2.imencode('.jpg', dummy_frame)
jpeg_bytes = jpeg.tobytes()

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        try:
            while True:
                self.wfile.write(b"--jpgboundary\r\n")
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(jpeg_bytes)))
                self.end_headers()
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b"\r\n")
                time.sleep(0.033) # ~30 FPS
        except Exception:
            pass
            
    def log_message(self, format, *args):
        return # Silenciar logs do HTTP server

def run_mjpeg_server():
    server = HTTPServer(('127.0.0.1', 9090), MJPEGHandler)
    server.serve_forever()

def add_cameras_to_svision(num_cameras):
    sock_path = "/tmp/svision-ui.sock"
    
    # Aguarda o SVISION iniciar o socket UDS
    for _ in range(30):
        if os.path.exists(sock_path):
            break
        time.sleep(1)
        
    if not os.path.exists(sock_path):
        print("[MOCK] Socket UDS não encontrado. Impossível adicionar câmeras.")
        return

    cameras = []
    # Testando troca de marca: simula diferentes marcas no payload
    brands = ["Intelbras", "Hikvision", "Axis", "Bosch", "Dahua"]
    for i in range(num_cameras):
        cam = {
            "id": f"mock_cam_{i}",
            "name": f"Câmera de Teste {i}",
            "address": "http://127.0.0.1:9090/stream",
            "brand": brands[i % len(brands)]
        }
        cameras.append(cam)

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(sock_path)
        payload = msgpack.packb({
            "topic": "set_cameras",
            "payload": cameras
        })
        # Framming de 4 bytes big-endian requerido pelo uds_router.py
        frame = struct.pack(">I", len(payload)) + payload
        client.sendall(frame)
        print(f"[MOCK] Injetado com sucesso {num_cameras} streams reais (MJPEG) para o SVISION CORE via UDS.")
        # Fecha a conexão rapidamente para devolver o socket ao Electron
        client.close()
    except Exception as e:
        print(f"[MOCK] Erro ao injetar câmeras: {e}")

def main():
    num_cameras = 20
    if len(sys.argv) > 1:
        try:
            num_cameras = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"Iniciando Mock de {num_cameras} câmeras enviando MJPEG real via HTTP...")
    
    # Inicia o servidor de stream de câmeras em background
    t = threading.Thread(target=run_mjpeg_server, daemon=True)
    t.start()
    
    # Injeta as câmeras no UDS do SVISION em outra thread
    t_inj = threading.Thread(target=add_cameras_to_svision, args=(num_cameras,), daemon=True)
    t_inj.start()
        
    try:
        print("Iniciando gerador de tráfego de PICO para forçar o SVISION CORE...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Mock de câmeras encerrado.")

if __name__ == "__main__":
    main()
