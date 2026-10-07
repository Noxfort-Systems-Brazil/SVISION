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

// File: uds_server_test.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"bufio"
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestUDSServer_SocketPermissions(t *testing.T) {
	tmpDir := t.TempDir()
	sockPath := filepath.Join(tmpDir, "uds_test_perm.sock")

	pm := NewPortManager("127.0.0.1", 9500, nil)
	server := NewUDSServer(sockPath, pm)
	if err := server.Start(); err != nil {
		t.Fatalf("failed to start UDS server: %v", err)
	}
	defer server.Stop()

	info, err := os.Stat(sockPath)
	if err != nil {
		t.Fatalf("failed to stat socket file: %v", err)
	}

	perm := info.Mode().Perm()
	if perm != 0600 {
		t.Fatalf("expected socket permissions 0600 (owner only), got %04o", perm)
	}
}

func TestUDSServer_CustomPermissions(t *testing.T) {
	t.Setenv("SVISION_SYNAPSE_UDS_MODE", "0660")

	tmpDir := t.TempDir()
	sockPath := filepath.Join(tmpDir, "uds_test_custom_perm.sock")

	pm := NewPortManager("127.0.0.1", 9500, nil)
	server := NewUDSServer(sockPath, pm)
	if err := server.Start(); err != nil {
		t.Fatalf("failed to start UDS server: %v", err)
	}
	defer server.Stop()

	info, err := os.Stat(sockPath)
	if err != nil {
		t.Fatalf("failed to stat socket file: %v", err)
	}

	perm := info.Mode().Perm()
	if perm != 0660 {
		t.Fatalf("expected socket permissions 0660, got %04o", perm)
	}
}

func TestUDSServer_CommandsFlow(t *testing.T) {
	tmpDir := t.TempDir()
	sockPath := filepath.Join(tmpDir, "uds_test_flow.sock")

	pm := NewPortManager("127.0.0.1", 9600, nil)
	server := NewUDSServer(sockPath, pm)
	if err := server.Start(); err != nil {
		t.Fatalf("failed to start server: %v", err)
	}
	defer server.Stop()

	conn, err := net.Dial("unix", sockPath)
	if err != nil {
		t.Fatalf("failed to connect to UDS server: %v", err)
	}
	defer conn.Close()

	reader := bufio.NewReader(conn)

	// 1. PING -> PONG
	_, _ = conn.Write([]byte("{\"cmd\":\"PING\"}\n"))
	line, err := reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read PING response: %v", err)
	}
	var pongResp UDSResponse
	if err := json.Unmarshal(line, &pongResp); err != nil {
		t.Fatalf("failed to parse PING response: %v", err)
	}
	if pongResp.Event != "PONG" || pongResp.Status != "OK" {
		t.Fatalf("unexpected PING response: %+v", pongResp)
	}

	// 2. ATTACH_CAMERA
	_, _ = conn.Write([]byte("{\"cmd\":\"ATTACH_CAMERA\",\"camera_id\":\"cam_uds_1\",\"sensor_id\":\"s_1\"}\n"))
	line, err = reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read ATTACH_CAMERA response: %v", err)
	}
	var attachResp UDSResponse
	if err := json.Unmarshal(line, &attachResp); err != nil {
		t.Fatalf("failed to parse ATTACH response: %v", err)
	}
	if attachResp.Event != "CAMERA_BOUND" || attachResp.CameraID != "cam_uds_1" || attachResp.Port != 9600 {
		t.Fatalf("unexpected ATTACH response: %+v", attachResp)
	}

	// 3. DETACH_CAMERA
	_, _ = conn.Write([]byte("{\"cmd\":\"DETACH_CAMERA\",\"camera_id\":\"cam_uds_1\"}\n"))
	line, err = reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read DETACH response: %v", err)
	}
	var detachResp UDSResponse
	if err := json.Unmarshal(line, &detachResp); err != nil {
		t.Fatalf("failed to parse DETACH response: %v", err)
	}
	if detachResp.Event != "CAMERA_DETACHED" || detachResp.Status != "CLOSED" {
		t.Fatalf("unexpected DETACH response: %+v", detachResp)
	}

	// 4. Invalid JSON
	_, _ = conn.Write([]byte("{invalid-json\n"))
	line, err = reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read invalid JSON response: %v", err)
	}
	var errResp UDSResponse
	if err := json.Unmarshal(line, &errResp); err != nil {
		t.Fatalf("failed to parse error response: %v", err)
	}
	if errResp.Event != "ERROR" {
		t.Fatalf("expected ERROR event, got: %+v", errResp)
	}

	// 5. Unknown command
	_, _ = conn.Write([]byte("{\"cmd\":\"UNKNOWN_CMD\"}\n"))
	line, err = reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read unknown cmd response: %v", err)
	}
	if err := json.Unmarshal(line, &errResp); err != nil {
		t.Fatalf("failed to parse unknown cmd response: %v", err)
	}
	if errResp.Event != "ERROR" {
		t.Fatalf("expected ERROR event for unknown cmd, got: %+v", errResp)
	}
}

func TestUDSServer_PortExhaustionResponse(t *testing.T) {
	tmpDir := t.TempDir()
	sockPath := filepath.Join(tmpDir, "uds_test_exhaust.sock")

	// Base port at MaxPort
	pm := NewPortManager("127.0.0.1", 65535, nil)
	server := NewUDSServer(sockPath, pm)
	if err := server.Start(); err != nil {
		t.Fatalf("failed to start server: %v", err)
	}
	defer server.Stop()

	conn, err := net.Dial("unix", sockPath)
	if err != nil {
		t.Fatalf("failed to connect: %v", err)
	}
	defer conn.Close()

	reader := bufio.NewReader(conn)

	// Attach first camera (port 65535)
	_, _ = conn.Write([]byte("{\"cmd\":\"ATTACH_CAMERA\",\"camera_id\":\"cam_first\"}\n"))
	line, err := reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read response: %v", err)
	}
	var resp1 UDSResponse
	_ = json.Unmarshal(line, &resp1)
	if resp1.Event != "CAMERA_BOUND" {
		t.Fatalf("expected CAMERA_BOUND for first camera, got: %+v", resp1)
	}

	// Attach second camera -> must fail with ERROR event
	_, _ = conn.Write([]byte("{\"cmd\":\"ATTACH_CAMERA\",\"camera_id\":\"cam_second\"}\n"))
	line, err = reader.ReadBytes('\n')
	if err != nil {
		t.Fatalf("failed to read response: %v", err)
	}
	var resp2 UDSResponse
	_ = json.Unmarshal(line, &resp2)
	if resp2.Event != "ERROR" {
		t.Fatalf("expected ERROR event due to port exhaustion, got: %+v", resp2)
	}
}

func TestUDSServer_BroadcastEvent_NonBlocking(t *testing.T) {
	tmpDir := t.TempDir()
	sockPath := filepath.Join(tmpDir, "uds_test_broadcast.sock")

	pm := NewPortManager("127.0.0.1", 9700, nil)
	server := NewUDSServer(sockPath, pm)
	if err := server.Start(); err != nil {
		t.Fatalf("failed to start server: %v", err)
	}
	defer server.Stop()

	// Client 1: active reader
	client1, err := net.Dial("unix", sockPath)
	if err != nil {
		t.Fatalf("client 1 failed to dial: %v", err)
	}
	defer client1.Close()

	// Client 2: slow/non-reading client
	client2, err := net.Dial("unix", sockPath)
	if err != nil {
		t.Fatalf("client 2 failed to dial: %v", err)
	}
	defer client2.Close()

	// Wait briefly for both clients to be registered in acceptLoop
	time.Sleep(50 * time.Millisecond)

	// Trigger broadcast
	doneCh := make(chan struct{})
	go func() {
		server.BroadcastEvent(UDSResponse{
			Event:    "STATUS_CHANGE",
			CameraID: "cam_test",
			Port:     9700,
			Status:   "CONNECTED",
		})
		close(doneCh)
	}()

	// Broadcast should complete quickly without hanging
	select {
	case <-doneCh:
		// Broadcast finished
	case <-time.After(1 * time.Second):
		t.Fatal("BroadcastEvent took more than 1 second; likely blocked on mutex or network I/O")
	}

	// Crucial test: acceptLoop must NOT be blocked while broadcasting or handling clients!
	client3, err := net.Dial("unix", sockPath)
	if err != nil {
		t.Fatalf("client 3 failed to connect to acceptLoop: %v", err)
	}
	defer client3.Close()

	// Verify client 1 receives the broadcasted event
	reader1 := bufio.NewReader(client1)
	_ = client1.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	line, err := reader1.ReadBytes('\n')
	if err != nil {
		t.Fatalf("client 1 failed to receive broadcast: %v", err)
	}
	var bResp UDSResponse
	if err := json.Unmarshal(line, &bResp); err != nil {
		t.Fatalf("failed to parse broadcast event: %v", err)
	}
	if bResp.Event != "STATUS_CHANGE" || bResp.Status != "CONNECTED" {
		t.Fatalf("unexpected broadcast event payload: %+v", bResp)
	}
}
