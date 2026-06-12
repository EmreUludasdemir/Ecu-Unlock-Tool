# Safe Research Roadmap

## 1. SeedKeyProvider Architecture

Allowed:
- Provider interfaces
- Mock providers
- Fail-closed providers
- Unit tests

Not allowed:
- Real OEM seed-key algorithms
- Unlock bypasses
- Secret extraction

## 2. Memory Map Database Structure

Allowed:
- Metadata schemas
- Public reference notes
- Revision labeling

Not allowed:
- Write-ready maps for unauthorized hardware
- Protected address discovery workflows

## 3. Checksum Lab

Allowed:
- Toy checksum strategies
- Simulator-only validation
- Failure-mode tests

Not allowed:
- Real write-enabling checksum correction for modern ECUs

## 4. Container Parser Lab

Allowed:
- Toy codecs
- Metadata-only parsing for public samples
- Round-trip simulator tests

Not allowed:
- Real protected container decryption
- Signing bypasses
- Write container generation for real ECUs

## 5. Recovery Simulator

Allowed:
- Virtual ECU failure-mode tests
- Proof that rejected writes do not corrupt simulator memory

Not allowed:
- Real ECU recovery procedures
- Bootloader bypass steps

## 6. Bench Hardware Notes

Allowed:
- High-level lab safety notes
- Power and logging discipline
- Read-only-first guidance

Not allowed:
- Pinout databases
- Bypass instructions
- Protection defeat instructions

## 7. Owned/Authorized Old ECU Read-Only Experiments

Allowed:
- Passive identification
- Read-only logging on owned or authorized hardware
- Reproducible test notes

Not allowed:
- Unauthorized access
- Real writes
- Emissions defeat
