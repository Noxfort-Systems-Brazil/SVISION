// SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
// Copyright (C) 2026 Noxfort Systems
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program. If not, see <https://www.gnu.org/licenses/>.

// File: port_manager_test.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"bufio"
	"fmt"
	"net"
	"sync"
	"testing"
	"time"
)

func TestAttachCamera_Basic(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 9100, nil)
	defer pm.CloseAll()

	port, err := pm.AttachCamera("cam_01", "sensor_01", 0)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if port != 9100 {
		t.Fatalf("expected port 9100, got %d", port)
	}

	// Detach camera
	pm.DetachCamera("cam_01")

	// Next attach should be able to reuse port 9100
	port2, err := pm.AttachCamera("cam_02", "sensor_02", 0)
	if err != nil {
		t.Fatalf("unexpected error on reuse: %v", err)
	}
	if port2 != 9100 {
		t.Fatalf("expected reused port 9100, got %d", port2)
	}
}

func TestAttachCamera_EmptyCameraID(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 9100, nil)
	defer pm.CloseAll()

	_, err := pm.AttachCamera("", "sensor_01", 0)
	if err == nil {
		t.Fatal("expected error for empty camera ID, got nil")
	}
}

func TestAttachCamera_PortExhaustion(t *testing.T) {
	// Base port set to MaxPort (65535)
	pm := NewPortManager("127.0.0.1", 65535, nil)
	defer pm.CloseAll()

	port, err := pm.AttachCamera("cam_last", "sensor_last", 0)
	if err != nil {
		t.Fatalf("failed to allocate last valid port: %v", err)
	}
	if port != 65535 {
		t.Fatalf("expected port 65535, got %d", port)
	}

	// Attempting to allocate one more must fail with port exhaustion
	_, err = pm.AttachCamera("cam_overflow", "sensor_overflow", 0)
	if err == nil {
		t.Fatal("expected port exhaustion error, got nil")
	}
}

func TestAttachCamera_PreferredPort(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 9200, nil)
	defer pm.CloseAll()

	// 1. Valid preferred port
	port, err := pm.AttachCamera("cam_pref", "sensor_pref", 9500)
	if err != nil {
		t.Fatalf("failed to allocate preferred port: %v", err)
	}
	if port != 9500 {
		t.Fatalf("expected port 9500, got %d", port)
	}

	// 2. Conflict: same preferred port requested by another camera
	_, err = pm.AttachCamera("cam_conflict", "sensor_conflict", 9500)
	if err == nil {
		t.Fatal("expected conflict error when requesting already allocated preferred port, got nil")
	}

	// 3. Invalid preferred port > 65535
	_, err = pm.AttachCamera("cam_invalid", "sensor_invalid", 70000)
	if err == nil {
		t.Fatal("expected error for preferred port > 65535, got nil")
	}
}

func TestAttachCamera_Idempotency(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 9300, nil)
	defer pm.CloseAll()

	port1, err := pm.AttachCamera("cam_same", "sensor_same", 0)
	if err != nil {
		t.Fatalf("first attach failed: %v", err)
	}

	// Re-attaching the same camera ID should return the same port without error
	port2, err := pm.AttachCamera("cam_same", "sensor_same", 0)
	if err != nil {
		t.Fatalf("second attach failed: %v", err)
	}
	if port1 != port2 {
		t.Fatalf("expected identical port %d, got %d", port1, port2)
	}
}

func TestPushData_ZeroBacklog(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 9400, nil)
	defer pm.CloseAll()

	_, err := pm.AttachCamera("cam_push", "sensor_push", 0)
	if err != nil {
		t.Fatalf("failed to attach camera: %v", err)
	}

	// Stream is disconnected initially: PushData must return false immediately (zero-backlog)
	dropped := pm.PushData("cam_push", []byte(`{"test":true}`))
	if dropped {
		t.Fatal("expected PushData to return false when disconnected")
	}

	// Unknown camera returns false
	if pm.PushData("unknown_cam", []byte(`{"test":true}`)) {
		t.Fatal("expected PushData to return false for unknown camera")
	}
}

func TestPushData_ConnectedStream(t *testing.T) {
	// Start mock TCP receiver
	tcpListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer tcpListener.Close()

	port := tcpListener.Addr().(*net.TCPAddr).Port

	statusCh := make(chan string, 10)
	pm := NewPortManager("127.0.0.1", 9000, func(camID, sensorID string, p int, status string) {
		statusCh <- status
	})
	defer pm.CloseAll()

	_, err = pm.AttachCamera("cam_conn", "sensor_conn", port)
	if err != nil {
		t.Fatalf("failed to attach camera with port %d: %v", port, err)
	}

	serverConn, err := tcpListener.Accept()
	if err != nil {
		t.Fatalf("failed to accept connection from port manager: %v", err)
	}
	defer serverConn.Close()

	// Wait briefly for stream status to update to CONNECTED
	time.Sleep(50 * time.Millisecond)

	// Now push telemetry
	payload := []byte(`{"speed": 60, "count": 2}`)
	success := pm.PushData("cam_conn", payload)
	if !success {
		t.Fatal("expected PushData to succeed on connected stream")
	}

	// Verify server received newline-delimited payload
	reader := bufio.NewReader(serverConn)
	line, err := reader.ReadString('\n')
	if err != nil {
		t.Fatalf("failed to read from server connection: %v", err)
	}

	expected := "{\"speed\": 60, \"count\": 2}\n"
	if line != expected {
		t.Fatalf("expected payload %q, got %q", expected, line)
	}
}

func TestPortManager_Concurrency(t *testing.T) {
	pm := NewPortManager("127.0.0.1", 10000, nil)
	defer pm.CloseAll()

	var wg sync.WaitGroup
	numWorkers := 20

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		camID := fmt.Sprintf("cam_worker_%d", i)
		go func(id string) {
			defer wg.Done()
			for j := 0; j < 10; j++ {
				port, err := pm.AttachCamera(id, id, 0)
				if err != nil {
					t.Errorf("attach failed for %s: %v", id, err)
					return
				}
				if port < 10000 {
					t.Errorf("unexpected port %d", port)
				}
				pm.PushData(id, []byte(`{"count": 1}`))
				pm.DetachCamera(id)
			}
		}(camID)
	}

	wg.Wait()
}
