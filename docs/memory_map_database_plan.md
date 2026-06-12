# Memory Map Database Plan

## Goal

Move ECU family/block metadata into a structured, testable database layer.

## What this branch implements

- MemoryBlockSpec
- EcuFamilySpec
- MemoryMapDatabase
- Mock metadata
- Simos18 read-only placeholder metadata
- Tests

## What this branch does not implement

- Real ECU unlock
- Real read/write support
- Exploits or bypasses
- Emissions defeat
- Real pinout/protocol database

## Why this matters

Professional tools need a protocol/ECU database. This branch models that concept
safely with toy/mock and read-only placeholder data.
