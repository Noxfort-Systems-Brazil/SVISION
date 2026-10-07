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

// File: port_allocator_test.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"sync"
	"testing"
)

func TestLinearPortAllocator_BasicAllocationAndRelease(t *testing.T) {
	alloc := NewLinearPortAllocator(9100)

	port1, err := alloc.Allocate(0)
	if err != nil {
		t.Fatalf("unexpected allocation error: %v", err)
	}
	if port1 != 9100 {
		t.Fatalf("expected port 9100, got %d", port1)
	}

	port2, err := alloc.Allocate(0)
	if err != nil {
		t.Fatalf("unexpected allocation error: %v", err)
	}
	if port2 != 9101 {
		t.Fatalf("expected port 9101, got %d", port2)
	}

	// Release port1 and re-allocate
	alloc.Release(port1)
	portReused, err := alloc.Allocate(0)
	if err != nil {
		t.Fatalf("unexpected allocation error after release: %v", err)
	}
	if portReused != 9100 {
		t.Fatalf("expected reused port 9100, got %d", portReused)
	}
}

func TestLinearPortAllocator_PreferredPort(t *testing.T) {
	alloc := NewLinearPortAllocator(9200)

	// Preferred allocation
	port, err := alloc.Allocate(9500)
	if err != nil {
		t.Fatalf("failed to allocate preferred port: %v", err)
	}
	if port != 9500 {
		t.Fatalf("expected port 9500, got %d", port)
	}

	// Conflict
	_, err = alloc.Allocate(9500)
	if err == nil {
		t.Fatal("expected conflict error when allocating already used preferred port")
	}

	// Exceeds MaxPort
	_, err = alloc.Allocate(70000)
	if err == nil {
		t.Fatal("expected error when preferred port > MaxPort")
	}
}

func TestLinearPortAllocator_PortExhaustion(t *testing.T) {
	alloc := NewLinearPortAllocator(65535)

	port, err := alloc.Allocate(0)
	if err != nil {
		t.Fatalf("failed to allocate last port: %v", err)
	}
	if port != 65535 {
		t.Fatalf("expected port 65535, got %d", port)
	}

	_, err = alloc.Allocate(0)
	if err == nil {
		t.Fatal("expected port exhaustion error, got nil")
	}
}

func TestLinearPortAllocator_ConcurrentAllocation(t *testing.T) {
	alloc := NewLinearPortAllocator(10000)
	var wg sync.WaitGroup
	workers := 50
	allocated := make(chan int, workers)

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			p, err := alloc.Allocate(0)
			if err == nil {
				allocated <- p
			}
		}()
	}

	wg.Wait()
	close(allocated)

	seen := make(map[int]bool)
	for p := range allocated {
		if seen[p] {
			t.Fatalf("duplicate port allocated concurrently: %d", p)
		}
		seen[p] = true
	}
	if len(seen) != workers {
		t.Fatalf("expected %d unique ports, got %d", workers, len(seen))
	}
}
