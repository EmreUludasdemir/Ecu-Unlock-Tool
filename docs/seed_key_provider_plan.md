# SeedKeyProvider Research Plan

## Goal

Explain safe seed-key provider architecture for AutoFlash.

## What this branch implements

- Provider interface
- Mock provider
- NoProvider
- Registry
- Tests

## What this branch does not implement

- Real OEM seed-key algorithms
- Exploits
- Secret extraction
- Unlock bypass

## Relation to UnlockECU

UnlockECU is a useful conceptual reference for understanding provider-based
seed-key tooling, but AutoFlash does not copy real provider algorithms or bypass
logic in this branch.
