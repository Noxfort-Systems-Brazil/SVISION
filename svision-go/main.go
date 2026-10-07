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

// File: main.go
// Author: Gabriel Moraes
// Date: 2026-03-27

package main

import (
	"flag"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"
)

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

func main() {
	defaultUDS := getEnv("SVISION_SYNAPSE_UDS_PATH", "/tmp/svision_synapse.sock")
	defaultHost := getEnv("SVISION_SYNAPSE_HOST", "127.0.0.1")
	defaultBasePortStr := getEnv("SVISION_SYNAPSE_BASE_PORT", "9001")
	defaultBasePort, _ := strconv.Atoi(defaultBasePortStr)
	if defaultBasePort <= 0 {
		defaultBasePort = 9001
	}

	udsPath := flag.String("uds", defaultUDS, "Path to Unix Domain Socket for Python IPC")
	synapseHost := flag.String("host", defaultHost, "Target Synapse server IP/hostname")
	basePort := flag.Int("base-port", defaultBasePort, "Starting port for camera TCP streams")
	flag.Parse()

	log.Println("==========================================================")
	log.Println("   SVision Synapse Dispatcher — Real-Time Network Gatekeeper")
	log.Println("==========================================================")
	log.Printf("UDS Socket:     %s", *udsPath)
	log.Printf("Synapse Host:   %s", *synapseHost)
	log.Printf("Base TCP Port:  %d", *basePort)

	var udsServer *UDSServer

	onStatusChange := func(camID, sensorID string, port int, status string) {
		if udsServer != nil {
			udsServer.BroadcastEvent(UDSResponse{
				Event:    "STATUS_CHANGE",
				CameraID: camID,
				SensorID: sensorID,
				Port:     port,
				Status:   status,
			})
		}
	}

	portManager := NewPortManager(*synapseHost, *basePort, onStatusChange)
	udsServer = NewUDSServer(*udsPath, portManager)

	if err := udsServer.Start(); err != nil {
		log.Fatalf("[FATAL] Failed to start UDS Server: %v", err)
	}

	// Trap termination signals
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	sig := <-sigCh
	log.Printf("[Synapse Dispatcher] Signal '%v' received. Initiating graceful shutdown...", sig)

	udsServer.Stop()
	portManager.CloseAll()

	log.Println("[Synapse Dispatcher] Shutdown complete.")
}
