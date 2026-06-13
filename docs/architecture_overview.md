# Architecture Overview

AutoFlash is organized as a safe educational ECU flashing framework.

## Core Flow

CLI or the demo script calls the Flasher. The Flasher uses a Connection
implementation and an ECUDriver plugin.

## Main Components

- Connection layer: virtual, OBD, bench, and boot abstractions
- VirtualECU: stateful UDS simulator for tests
- ECUDriver: platform-specific contract
- MockDriver: virtual-only driver
- SeedKeyProvider: mock seed-key provider architecture
- Checksum strategy: toy CRC32 lab
- Container codec: toy XOR lab
- Memory map database: safe ECU family/block metadata
- Capabilities: explicit driver safety policy
- Operation plan: inspectable write plan
- Dry-run: no memory modification
- Audit log: JSONL operation log

## Safety Boundary

This repository does not implement real ECU unlock exploits, real OEM seed-key
algorithms, protection bypasses, boot password recovery, emissions defeat, or
real ECU write support.
