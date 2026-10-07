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

// File: uds_server.go
// Author: Gabriel Moraes
// Date: 2026-03-27

package main

import (
	"bufio"
	"encoding/json"
	"log"
	"net"
	"os"
	"strconv"
	"sync"
	"time"
)

// UDSRequest defines the schema for incoming commands from Python.
type UDSRequest struct {
	Cmd           string          `json:"cmd"`
	CameraID      string          `json:"camera_id,omitempty"`
	SensorID      string          `json:"sensor_id,omitempty"`
	PreferredPort int             `json:"preferred_port,omitempty"`
	Payload       json.RawMessage `json:"payload,omitempty"`
	SynapseHost   string          `json:"synapse_host,omitempty"`
}

// UDSResponse defines the schema for outgoing events sent to Python.
type UDSResponse struct {
	Event    string `json:"event"`
	CameraID string `json:"camera_id,omitempty"`
	SensorID string `json:"sensor_id,omitempty"`
	Port     int    `json:"port,omitempty"`
	Status   string `json:"status,omitempty"`
	Error    string `json:"error,omitempty"`
}

// UDSServer handles local IPC with Python via Unix Domain Socket.
type UDSServer struct {
	socketPath  string
	listener    net.Listener
	portManager StreamManager
	clients     map[net.Conn]*sync.Mutex
	mu          sync.Mutex
	stopCh      chan struct{}
}

// NewUDSServer initializes the UDS server.
func NewUDSServer(socketPath string, pm StreamManager) *UDSServer {
	return &UDSServer{
		socketPath:  socketPath,
		portManager: pm,
		clients:     make(map[net.Conn]*sync.Mutex),
		stopCh:      make(chan struct{}),
	}
}

// Start starts listening on the Unix Domain Socket.
func (s *UDSServer) Start() error {
	// Remove stale socket if present
	_ = os.Remove(s.socketPath)

	listener, err := net.Listen("unix", s.socketPath)
	if err != nil {
		return err
	}
	s.listener = listener

	// Secure socket permissions: restrict to owner (0600) so unprivileged local processes cannot connect.
	// Can be overridden via SVISION_SYNAPSE_UDS_MODE environment variable if needed.
	socketMode := os.FileMode(0600)
	if envMode := os.Getenv("SVISION_SYNAPSE_UDS_MODE"); envMode != "" {
		if parsed, err := strconv.ParseUint(envMode, 8, 32); err == nil {
			socketMode = os.FileMode(parsed)
		}
	}
	_ = os.Chmod(s.socketPath, socketMode)

	log.Printf("[UDSServer] Listening on %s (mode: %04o)", s.socketPath, socketMode)

	go s.acceptLoop()
	return nil
}

func (s *UDSServer) acceptLoop() {
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			select {
			case <-s.stopCh:
				return
			default:
				log.Printf("[UDSServer] Accept error: %v", err)
				return
			}
		}

		connMu := &sync.Mutex{}
		s.mu.Lock()
		s.clients[conn] = connMu
		s.mu.Unlock()

		log.Printf("[UDSServer] Python client connected")
		go s.handleClient(conn, connMu)
	}
}

func (s *UDSServer) handleClient(conn net.Conn, writeMu *sync.Mutex) {
	defer func() {
		s.mu.Lock()
		delete(s.clients, conn)
		s.mu.Unlock()
		conn.Close()
		log.Printf("[UDSServer] Python client disconnected")
	}()

	scanner := bufio.NewScanner(conn)
	// Support payloads up to 1MB
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, 1024*1024)

	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}

		var req UDSRequest
		if err := json.Unmarshal(line, &req); err != nil {
			s.sendResponseTo(conn, writeMu, UDSResponse{
				Event: "ERROR",
				Error: "Invalid JSON format: " + err.Error(),
			})
			continue
		}

		s.processCommand(conn, writeMu, req)
	}

	if err := scanner.Err(); err != nil {
		log.Printf("[UDSServer] Scanner read error: %v", err)
	}
}

func (s *UDSServer) processCommand(conn net.Conn, writeMu *sync.Mutex, req UDSRequest) {
	switch req.Cmd {
	case "ATTACH_CAMERA":
		port, err := s.portManager.AttachCamera(req.CameraID, req.SensorID, req.PreferredPort)
		if err != nil {
			s.sendResponseTo(conn, writeMu, UDSResponse{
				Event:    "ERROR",
				CameraID: req.CameraID,
				Error:    err.Error(),
			})
			return
		}
		s.sendResponseTo(conn, writeMu, UDSResponse{
			Event:    "CAMERA_BOUND",
			CameraID: req.CameraID,
			SensorID: req.SensorID,
			Port:     port,
			Status:   "READY",
		})

	case "DETACH_CAMERA":
		s.portManager.DetachCamera(req.CameraID)
		s.sendResponseTo(conn, writeMu, UDSResponse{
			Event:    "CAMERA_DETACHED",
			CameraID: req.CameraID,
			Status:   "CLOSED",
		})

	case "DATA":
		if req.CameraID != "" && len(req.Payload) > 0 {
			s.portManager.PushData(req.CameraID, req.Payload)
		}

	case "UPDATE_CONFIG":
		if req.SynapseHost != "" {
			s.portManager.SetHost(req.SynapseHost)
			s.sendResponseTo(conn, writeMu, UDSResponse{
				Event:  "CONFIG_UPDATED",
				Status: "OK",
			})
		}

	case "PING":
		s.sendResponseTo(conn, writeMu, UDSResponse{
			Event:  "PONG",
			Status: "OK",
		})

	default:
		s.sendResponseTo(conn, writeMu, UDSResponse{
			Event: "ERROR",
			Error: "Unknown command: " + req.Cmd,
		})
	}
}

type clientTarget struct {
	conn    net.Conn
	writeMu *sync.Mutex
}

// BroadcastEvent broadcasts an event message to all connected Python clients.
// It snapshots active clients under lock and releases s.mu BEFORE performing network I/O,
// ensuring slow or stalled client writes never block the acceptLoop or client cleanups.
func (s *UDSServer) BroadcastEvent(resp UDSResponse) {
	data, err := json.Marshal(resp)
	if err != nil {
		return
	}
	data = append(data, '\n')

	s.mu.Lock()
	targets := make([]clientTarget, 0, len(s.clients))
	for conn, writeMu := range s.clients {
		targets = append(targets, clientTarget{conn: conn, writeMu: writeMu})
	}
	s.mu.Unlock()

	for _, target := range targets {
		target.writeMu.Lock()
		_ = target.conn.SetWriteDeadline(time.Now().Add(100 * time.Millisecond))
		_, _ = target.conn.Write(data)
		target.writeMu.Unlock()
	}
}

func (s *UDSServer) sendResponseTo(conn net.Conn, writeMu *sync.Mutex, resp UDSResponse) {
	data, err := json.Marshal(resp)
	if err != nil {
		return
	}
	data = append(data, '\n')

	writeMu.Lock()
	_ = conn.SetWriteDeadline(time.Now().Add(100 * time.Millisecond))
	_, _ = conn.Write(data)
	writeMu.Unlock()
}

// Stop gracefully shuts down the UDS listener and removes the socket file.
func (s *UDSServer) Stop() {
	close(s.stopCh)
	if s.listener != nil {
		s.listener.Close()
	}
	s.mu.Lock()
	for conn := range s.clients {
		conn.Close()
	}
	s.clients = make(map[net.Conn]*sync.Mutex)
	s.mu.Unlock()

	_ = os.Remove(s.socketPath)
	log.Printf("[UDSServer] Stopped and removed socket %s", s.socketPath)
}
