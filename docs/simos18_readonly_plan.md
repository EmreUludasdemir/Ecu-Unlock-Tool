# Simos18 Read-Only Integration Plan

## Goal

This branch explores a safe, read-only Simos18 integration path for AutoFlash.

The goal is not to unlock or bypass modern ECU protections. The goal is to
understand how an ECU-specific driver can be structured around identification,
memory map documentation, container metadata, checksum mapping notes, and safe
read-only analysis.

## Scope

Allowed:
- Simos18 driver structure cleanup
- Identification-related TODOs
- Read-only memory map notes
- Container/checksum mapping notes
- Public open-source references
- Safe stub methods
- Tests that ensure write/security-sensitive methods remain disabled

Not allowed:
- Real seed-key exploit implementation
- RSA bypass implementation
- CBOOT/SBOOT patching
- Boot password recovery
- Modern MG1/MD1 unlock
- Emissions defeat
- Writing to a real ECU

## References

- bri3d/VW_Flash
- bri3d/Simos18_SBOOT
- AutoFlash mock driver and virtual ECU tests

## Driver Mapping

### `identify`

Current status:
- Reads basic identity information where a standard UDS client exposes it.
- Currently returns a minimal `EcuInfo(name="Simos18")` and best-effort VIN.

Safe read-only target:
- Document the DIDs used for identification.
- Add non-invasive reads for software and hardware metadata when supported by
  owned or authorized hardware.
- Keep identification as a passive read-only operation.

What must stay unimplemented for now:
- Any identification flow that depends on unlocking, patching, or bypassing
  protected ECU state.

### `memory_map`

Current status:
- Returns placeholder CAL and ASW1 blocks.
- Addresses and sizes are illustrative and must not be treated as authoritative.

Safe read-only target:
- Document known public memory layout notes and revision-specific differences.
- Keep the map as metadata until it is validated against public samples or
  owned/authorized hardware.

What must stay unimplemented for now:
- Any write/recovery assumptions or block layout that enables flashing a real ECU.

### `compute_key`

Current status:
- Intentionally raises `NotImplementedError`.

Safe read-only target:
- Document that SecurityAccess is outside this branch.
- Keep tests proving no seed-key logic is provided.

What must stay unimplemented for now:
- Real seed-key logic, unlock logic, bypass logic, exploit code, or protected
  access enablement.

### `decode_container`

Current status:
- Intentionally raises `NotImplementedError`.

Safe read-only target:
- Track public notes about container structure and metadata fields.
- Optionally add metadata-only parsing for known public sample files later.

What must stay unimplemented for now:
- Any protected container decryption/decompression implementation that enables
  unauthorized access to modern ECU contents.

### `encode_container`

Current status:
- Intentionally raises `NotImplementedError`.

Safe read-only target:
- Stay disabled in this branch.
- Keep tests proving the write preparation path cannot run.

What must stay unimplemented for now:
- Compression, encryption, signing, patching, or any path that prepares bytes for
  writing to a real ECU.

### `correct_checksum`

Current status:
- Intentionally raises `NotImplementedError`.

Safe read-only target:
- Document checksum families and mapping notes at a high level.
- Keep checksum correction disabled until the project has a separate safe scope.

What must stay unimplemented for now:
- Real checksum correction that enables write/recovery on real hardware.

## Milestones

1. Document Simos18 driver boundaries.
2. Keep write/security-sensitive methods disabled.
3. Add tests proving dangerous methods raise `NotImplementedError`.
4. Later, optionally add metadata-only parsing for known public sample files.
5. Only after that, consider read-only experiments on owned/authorized hardware.
