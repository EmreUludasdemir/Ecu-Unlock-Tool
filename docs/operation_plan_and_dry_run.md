# Operation Plan and Dry-Run

## Goal

Make write-like operations explicit, inspectable, and safe.

## What this branch implements

- OperationPlan
- BlockOperation
- Write plan preview
- CLI --plan
- CLI --dry-run
- JSONL audit log
- Tests

## Why this matters

Real flashing tools should make dangerous operations visible before execution.
AutoFlash models that idea safely using the virtual ECU and mock driver.

## Safety policy

- Dry-run never calls `flasher.write`.
- Plan mode never modifies ECU memory.
- Real ECU write support is still not implemented.
- Mock write is virtual-only.
- Simos18 remains read-only/research stub.
