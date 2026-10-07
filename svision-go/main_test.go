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

// File: main_test.go
// Author: Gabriel Moraes
// Date: 2026-09-05

package main

import (
	"os"
	"strconv"
	"testing"
)

func TestGetEnv_Fallback(t *testing.T) {
	key := "TEST_SVISION_NON_EXISTENT_VAR_XYZ"
	fallback := "default_fallback_val"

	// Ensure var is unset
	_ = os.Unsetenv(key)

	result := getEnv(key, fallback)
	if result != fallback {
		t.Fatalf("expected fallback %q, got %q", fallback, result)
	}
}

func TestGetEnv_Existing(t *testing.T) {
	key := "TEST_SVISION_CUSTOM_ENV_VAR"
	expected := "my_custom_value"

	_ = os.Setenv(key, expected)
	defer os.Unsetenv(key)

	result := getEnv(key, "other_fallback")
	if result != expected {
		t.Fatalf("expected custom value %q, got %q", expected, result)
	}
}

func TestDefaultBasePortParsing(t *testing.T) {
	testCases := []struct {
		envVal   string
		expected int
	}{
		{"9005", 9005},
		{"0", 9001},
		{"-10", 9001},
		{"invalid", 9001},
		{"", 9001},
	}

	for _, tc := range testCases {
		val := tc.envVal
		if val == "" {
			val = "9001"
		}
		port, _ := strconv.Atoi(val)
		if port <= 0 {
			port = 9001
		}
		if port != tc.expected {
			t.Errorf("for input %q expected %d, got %d", tc.envVal, tc.expected, port)
		}
	}
}
