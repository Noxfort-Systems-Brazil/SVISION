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
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// File: camera_stream_test.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"bufio"
	"net"
	"testing"
	"time"
)

// mockDialer implements StreamDialer using an in-memory net.Pipe, proving DIP without opening OS sockets.
type mockDialer struct {
	serverSide net.Conn
}

func (m *mockDialer) Dial(network, address string, timeout time.Duration) (net.Conn, error) {
	clientConn, serverConn := net.Pipe()
	m.serverSide = serverConn
	return clientConn, nil
}

func TestCameraStream_MockDialerPushAndFraming(t *testing.T) {
	mock := &mockDialer{}
	statusCh := make(chan string, 5)

	stream := NewCameraStream("cam_mock", "sensor_mock", "mockhost", 9999, mock, func(c, s string, p int, status string) {
		statusCh <- status
	})
	defer stream.Close()

	// Initial status is CONNECTING
	if stream.Status() != "CONNECTING" {
		t.Fatalf("expected initial status CONNECTING, got %s", stream.Status())
	}

	// Trigger connection with mock dialer
	stream.tryConnect()

	if stream.Status() != "CONNECTED" {
		t.Fatalf("expected status CONNECTED after tryConnect, got %s", stream.Status())
	}

	// Read from the server side in background
	receivedCh := make(chan string, 1)
	go func() {
		reader := bufio.NewReader(mock.serverSide)
		line, _ := reader.ReadString('\n')
		receivedCh <- line
	}()

	// Push telemetry payload without newline
	payload := []byte(`{"event":"test"}`)
	pushed := stream.Push(payload)
	if !pushed {
		t.Fatal("expected Push to succeed")
	}

	select {
	case line := <-receivedCh:
		expected := "{\"event\":\"test\"}\n"
		if line != expected {
			t.Fatalf("expected framed payload %q, got %q", expected, line)
		}
	case <-time.After(500 * time.Millisecond):
		t.Fatal("timed out waiting for framed telemetry on mock server side")
	}
}

func TestCameraStream_ZeroBacklogWhenDisconnected(t *testing.T) {
	stream := NewCameraStream("cam_disc", "sensor_disc", "nowhere", 9998, nil, nil)
	defer stream.Close()

	// Initially conn is nil: push must return false immediately (zero-backlog)
	if stream.Push([]byte(`{"ping":1}`)) {
		t.Fatal("expected Push to drop data when disconnected")
	}
}
