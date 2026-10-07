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

// File: camera_stream.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"fmt"
	"log"
	"net"
	"sync"
	"time"
)

// StreamDialer abstracts network connection dialing.
// Adheres to DIP: allows injecting mock dialers for unit tests and enables future TLS/mTLS support.
type StreamDialer interface {
	Dial(network, address string, timeout time.Duration) (net.Conn, error)
}

// DefaultTCPDialer connects via TCP and configures low-latency socket options.
type DefaultTCPDialer struct{}

// Dial establishes a TCP connection with TCP_NODELAY and KeepAlive.
func (d *DefaultTCPDialer) Dial(network, address string, timeout time.Duration) (net.Conn, error) {
	dialer := net.Dialer{Timeout: timeout}
	conn, err := dialer.Dial(network, address)
	if err != nil {
		return nil, err
	}

	if tcpConn, ok := conn.(*net.TCPConn); ok {
		_ = tcpConn.SetNoDelay(true)
		_ = tcpConn.SetKeepAlive(true)
		_ = tcpConn.SetKeepAlivePeriod(10 * time.Second)
	}
	return conn, nil
}

// CameraStream encapsulates an isolated outbound TCP push stream for a single camera.
// Encapsulates its own connection lifecycle, reconnection worker, framing, and status updates.
type CameraStream struct {
	CameraID string
	SensorID string
	Port     int

	mu             sync.Mutex
	host           string
	conn           net.Conn
	dialer         StreamDialer
	stopCh         chan struct{}
	status         string
	isClosed       bool
	onStatusChange func(camID, sensorID string, port int, status string)
}

// NewCameraStream creates a new encapsulated CameraStream instance.
func NewCameraStream(
	cameraID, sensorID, host string,
	port int,
	dialer StreamDialer,
	onStatus func(string, string, int, string),
) *CameraStream {
	if dialer == nil {
		dialer = &DefaultTCPDialer{}
	}
	return &CameraStream{
		CameraID:       cameraID,
		SensorID:       sensorID,
		Port:           port,
		host:           host,
		dialer:         dialer,
		stopCh:         make(chan struct{}),
		status:         "CONNECTING",
		onStatusChange: onStatus,
	}
}

// Start launches the background worker maintaining the connection to Synapse.
func (s *CameraStream) Start() {
	go s.runWorker()
}

// SetHost dynamically updates the target Synapse host for reconnections.
func (s *CameraStream) SetHost(host string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.host = host
}

// Status returns the current connection status.
func (s *CameraStream) Status() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.status
}

// Push writes a telemetry payload to the TCP stream.
// Strict Real-Time Policy: Zero-backlog. If not connected, drops immediately.
func (s *CameraStream) Push(payload []byte) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.isClosed || s.conn == nil {
		return false
	}

	// 100ms strict timeout for live telemetry write
	_ = s.conn.SetWriteDeadline(time.Now().Add(100 * time.Millisecond))

	// Ensure newline delimiter for NDJSON stream framing
	var msg []byte
	if len(payload) > 0 && payload[len(payload)-1] == '\n' {
		msg = payload
	} else {
		msg = append(payload, '\n')
	}

	_, err := s.conn.Write(msg)
	if err != nil {
		log.Printf("[CameraStream] [%s] Write failed (%v) — closing connection and dropping packet", s.CameraID, err)
		s.conn.Close()
		s.conn = nil
		s.updateStatusLocked("DISCONNECTED")
		return false
	}

	return true
}

// Close gracefully stops the worker, closes any open socket, and marks status as CLOSED.
func (s *CameraStream) Close() {
	s.mu.Lock()
	if s.isClosed {
		s.mu.Unlock()
		return
	}
	s.isClosed = true
	select {
	case <-s.stopCh:
	default:
		close(s.stopCh)
	}
	if s.conn != nil {
		s.conn.Close()
		s.conn = nil
	}
	s.updateStatusLocked("CLOSED")
	s.mu.Unlock()
}

func (s *CameraStream) runWorker() {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	// Initial immediate connection attempt
	s.tryConnect()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ticker.C:
			s.mu.Lock()
			needConnect := (!s.isClosed && s.conn == nil)
			s.mu.Unlock()

			if needConnect {
				s.tryConnect()
			}
		}
	}
}

func (s *CameraStream) tryConnect() {
	s.mu.Lock()
	if s.isClosed {
		s.mu.Unlock()
		return
	}
	host := s.host
	port := s.Port
	dialer := s.dialer
	s.mu.Unlock()

	target := fmt.Sprintf("%s:%d", host, port)
	conn, err := dialer.Dial("tcp", target, 1500*time.Millisecond)
	if err != nil {
		s.mu.Lock()
		if s.status != "DISCONNECTED" && !s.isClosed {
			s.updateStatusLocked("DISCONNECTED")
		}
		s.mu.Unlock()
		return
	}

	s.mu.Lock()
	if s.isClosed {
		conn.Close()
		s.mu.Unlock()
		return
	}
	s.conn = conn
	s.updateStatusLocked("CONNECTED")
	log.Printf("[CameraStream] [%s] Successfully connected to Synapse at %s", s.CameraID, target)
	s.mu.Unlock()
}

func (s *CameraStream) updateStatusLocked(newStatus string) {
	s.status = newStatus
	if s.onStatusChange != nil {
		cb := s.onStatusChange
		camID := s.CameraID
		sensorID := s.SensorID
		port := s.Port
		go cb(camID, sensorID, port, newStatus)
	}
}
