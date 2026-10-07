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

// File: port_allocator.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"fmt"
	"sync"
)

const (
	// MaxPort defines the maximum valid TCP port.
	MaxPort = 65535
	// DefaultBasePort defines the fallback starting port.
	DefaultBasePort = 9001
)

// PortAllocator defines the contract for reserving and freeing TCP ports.
// Adheres to DIP & OCP: allows swapping allocation strategies or mocking in tests.
type PortAllocator interface {
	Allocate(preferred int) (int, error)
	Release(port int)
}

// LinearPortAllocator implements PortAllocator with sequential port scanning.
type LinearPortAllocator struct {
	mu        sync.Mutex
	basePort  int
	maxPort   int
	usedPorts map[int]bool
}

// NewLinearPortAllocator creates a new thread-safe LinearPortAllocator.
func NewLinearPortAllocator(basePort int) *LinearPortAllocator {
	if basePort <= 0 {
		basePort = DefaultBasePort
	}
	return &LinearPortAllocator{
		basePort:  basePort,
		maxPort:   MaxPort,
		usedPorts: make(map[int]bool),
	}
}

// Allocate reserves the preferred port if requested or finds the next available port from basePort.
func (a *LinearPortAllocator) Allocate(preferred int) (int, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if preferred > 0 {
		if preferred > a.maxPort {
			return 0, fmt.Errorf("preferred port %d exceeds maximum valid TCP port (%d)", preferred, a.maxPort)
		}
		if a.usedPorts[preferred] {
			return 0, fmt.Errorf("preferred port %d is already in use", preferred)
		}
		a.usedPorts[preferred] = true
		return preferred, nil
	}

	if a.basePort < 1 || a.basePort > a.maxPort {
		return 0, fmt.Errorf("invalid base port %d: must be between 1 and %d", a.basePort, a.maxPort)
	}

	candidate := a.basePort
	for a.usedPorts[candidate] {
		candidate++
		if candidate > a.maxPort {
			return 0, fmt.Errorf("port exhaustion: no available ports up to %d", a.maxPort)
		}
	}

	a.usedPorts[candidate] = true
	return candidate, nil
}

// Release frees the given port for future reuse.
func (a *LinearPortAllocator) Release(port int) {
	a.mu.Lock()
	defer a.mu.Unlock()
	delete(a.usedPorts, port)
}
