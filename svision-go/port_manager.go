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

// File: port_manager.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"fmt"
	"log"
	"sync"
)

// StreamManager defines the consumer interface for managing camera telemetry streams.
// Adheres to LSP and ISP: decoupled from the concrete PortManager struct.
type StreamManager interface {
	AttachCamera(cameraID, sensorID string, preferredPort int) (int, error)
	DetachCamera(cameraID string)
	PushData(cameraID string, payload []byte) bool
	SetHost(host string)
	CloseAll()
}

// PortManager coordinates dedicated TCP push streams for each camera.
// Acts as a pure orchestrator delegating port allocation to PortAllocator and
// network lifecycle to CameraStream (Single Responsibility Principle).
type PortManager struct {
	mu             sync.RWMutex
	synapseHost    string
	allocator      PortAllocator
	dialer         StreamDialer
	cameras        map[string]*CameraStream
	onStatusChange func(camID string, sensorID string, port int, status string)
}

// NewPortManager creates a new PortManager instance with default production dependencies.
// Preserves 100% backward compatibility with main.go and existing tests.
func NewPortManager(host string, basePort int, onStatus func(string, string, int, string)) *PortManager {
	allocator := NewLinearPortAllocator(basePort)
	dialer := &DefaultTCPDialer{}
	return NewPortManagerWithDependencies(host, allocator, dialer, onStatus)
}

// NewPortManagerWithDependencies creates a PortManager with explicit dependencies (Dependency Inversion Principle).
// Enables seamless unit testing with mock allocators and mock dialers.
func NewPortManagerWithDependencies(
	host string,
	allocator PortAllocator,
	dialer StreamDialer,
	onStatus func(string, string, int, string),
) *PortManager {
	return &PortManager{
		synapseHost:    host,
		allocator:      allocator,
		dialer:         dialer,
		cameras:        make(map[string]*CameraStream),
		onStatusChange: onStatus,
	}
}

// SetHost updates the Synapse destination host for new and existing reconnecting streams.
func (pm *PortManager) SetHost(host string) {
	pm.mu.Lock()
	pm.synapseHost = host
	streams := make([]*CameraStream, 0, len(pm.cameras))
	for _, s := range pm.cameras {
		streams = append(streams, s)
	}
	pm.mu.Unlock()

	for _, s := range streams {
		s.SetHost(host)
	}
	log.Printf("[PortManager] Synapse host updated to: %s", host)
}

// AttachCamera registers a camera and starts its dedicated push connection loop.
func (pm *PortManager) AttachCamera(cameraID, sensorID string, preferredPort int) (int, error) {
	if cameraID == "" {
		return 0, fmt.Errorf("camera ID cannot be empty")
	}

	pm.mu.Lock()
	defer pm.mu.Unlock()

	if sensorID == "" {
		sensorID = cameraID
	}

	// Idempotency: if already registered, return existing port
	if existing, found := pm.cameras[cameraID]; found {
		return existing.Port, nil
	}

	// Allocate port via injected PortAllocator
	port, err := pm.allocator.Allocate(preferredPort)
	if err != nil {
		return 0, err
	}

	stream := NewCameraStream(cameraID, sensorID, pm.synapseHost, port, pm.dialer, pm.onStatusChange)
	pm.cameras[cameraID] = stream

	log.Printf("[PortManager] Attached camera '%s' (SensorID: '%s') -> Synapse target %s:%d",
		cameraID, sensorID, pm.synapseHost, port)

	// Launch dedicated connection worker
	stream.Start()

	if pm.onStatusChange != nil {
		pm.onStatusChange(cameraID, sensorID, port, "CONNECTING")
	}

	return port, nil
}

// DetachCamera closes and unregisters the camera's TCP push stream and frees its port.
func (pm *PortManager) DetachCamera(cameraID string) {
	pm.mu.Lock()
	stream, found := pm.cameras[cameraID]
	if !found {
		pm.mu.Unlock()
		return
	}

	delete(pm.cameras, cameraID)
	pm.allocator.Release(stream.Port)
	pm.mu.Unlock()

	stream.Close()
	log.Printf("[PortManager] Detached camera '%s' (freed port %d)", cameraID, stream.Port)
}

// PushData pushes a telemetry payload to the camera's dedicated TCP stream.
// Strict Real-Time Policy: Zero-backlog. If not connected, drop immediately.
func (pm *PortManager) PushData(cameraID string, payload []byte) bool {
	pm.mu.RLock()
	stream, found := pm.cameras[cameraID]
	pm.mu.RUnlock()

	if !found {
		return false
	}
	return stream.Push(payload)
}

// CloseAll closes all active streams, releases all reserved ports, and cleans up resources.
func (pm *PortManager) CloseAll() {
	pm.mu.Lock()
	streamsToClose := make([]*CameraStream, 0, len(pm.cameras))
	for _, s := range pm.cameras {
		streamsToClose = append(streamsToClose, s)
		pm.allocator.Release(s.Port)
	}
	pm.cameras = make(map[string]*CameraStream)
	pm.mu.Unlock()

	for _, stream := range streamsToClose {
		stream.Close()
	}
}
