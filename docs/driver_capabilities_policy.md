# Driver Capabilities and Safety Policy

## Goal

Make each ECU driver explicitly declare what it supports.

## Why this matters

Professional flashing tools must know whether a driver is virtual-only,
read-only, experimental, or real-hardware capable. AutoFlash models this safely.

## Capability fields

- safety_level
- supported_connection_modes
- identify_supported
- read_supported
- write_supported
- security_access_supported
- real_ecu_supported
- notes

## Safety policy

Mock driver may support virtual write, but not real ECU write.

Simos18 remains read-only/research stub.

No driver in this repository currently supports real ECU unlock or real ECU
write.

## Not implemented

- OEM seed-key algorithms
- Unlock bypasses
- RSA/SBOOT/CBOOT patches
- Boot password recovery
- Emissions defeat
