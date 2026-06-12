"""Operation planning and audit logging for write-like workflows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class OperationPlanError(ValueError):
    """Raised when an operation plan cannot be built safely."""


class OperationType(str, Enum):
    IDENTIFY = "identify"
    READ = "read"
    WRITE = "write"
    CAPABILITIES = "capabilities"


@dataclass(frozen=True)
class BlockOperation:
    block_name: str
    address: int
    expected_size: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "block_name": self.block_name,
            "address": self.address,
            "expected_size": self.expected_size,
            "file_path": self.file_path,
            "file_size": self.file_size,
        }


@dataclass(frozen=True)
class OperationPlan:
    operation_type: OperationType
    driver_name: str
    connection_mode: str
    safety_level: str
    real_ecu_supported: bool
    write_supported: bool
    allows_write: bool
    dry_run: bool = False
    blocks: tuple[BlockOperation, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "operation_type": self.operation_type.value,
            "driver_name": self.driver_name,
            "connection_mode": self.connection_mode,
            "safety_level": self.safety_level,
            "real_ecu_supported": self.real_ecu_supported,
            "write_supported": self.write_supported,
            "allows_write": self.allows_write,
            "dry_run": self.dry_run,
            "blocks": [block.to_dict() for block in self.blocks],
            "notes": self.notes,
        }

    def to_text(self) -> str:
        lines = [
            f"operation: {self.operation_type.value}",
            f"driver: {self.driver_name}",
            f"connection_mode: {self.connection_mode}",
            f"safety_level: {self.safety_level}",
            f"real_ecu_supported: {str(self.real_ecu_supported).lower()}",
            f"write_supported: {str(self.write_supported).lower()}",
            f"allows_write: {str(self.allows_write).lower()}",
            f"dry_run: {str(self.dry_run).lower()}",
        ]
        for block in self.blocks:
            lines.extend(
                [
                    f"block: {block.block_name}",
                    f"address: 0x{block.address:08X}",
                    f"expected_size: {block.expected_size}",
                    f"file_path: {block.file_path}",
                    f"file_size: {block.file_size}",
                ]
            )
        if self.notes:
            lines.append(f"notes: {self.notes}")
        return "\n".join(lines)


class OperationPlanner:
    """Build inspectable plans before write-like operations."""

    def plan_write(self, driver, connection, files: dict, dry_run: bool) -> OperationPlan:
        caps = driver.capabilities()
        blocks = []
        memory_blocks = {block.name: block for block in driver.memory_map()}
        for block_name, file_path in files.items():
            block = memory_blocks.get(block_name)
            if block is None:
                raise OperationPlanError(f"Unknown memory block: {block_name}")
            if not os.path.isfile(file_path):
                raise OperationPlanError(f"File not found: {file_path}")
            blocks.append(
                BlockOperation(
                    block_name=block.name,
                    address=block.address,
                    expected_size=block.size,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                )
            )
        return OperationPlan(
            operation_type=OperationType.WRITE,
            driver_name=caps.driver_name,
            connection_mode=getattr(connection, "mode", "unknown"),
            safety_level=caps.safety_level.value,
            real_ecu_supported=caps.real_ecu_supported,
            write_supported=caps.write_supported,
            allows_write=caps.allows_write(),
            dry_run=dry_run,
            blocks=tuple(blocks),
            notes=caps.notes,
        )


@dataclass(frozen=True)
class AuditLogEntry:
    timestamp: str
    operation_type: OperationType
    driver_name: str
    dry_run: bool
    success: bool
    message: str
    plan: dict

    @classmethod
    def from_plan(
        cls,
        plan: OperationPlan,
        success: bool,
        message: str,
    ) -> "AuditLogEntry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation_type=plan.operation_type,
            driver_name=plan.driver_name,
            dry_run=plan.dry_run,
            success=success,
            message=message,
            plan=plan.to_dict(),
        )

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation_type": self.operation_type.value,
            "driver_name": self.driver_name,
            "dry_run": self.dry_run,
            "success": self.success,
            "message": self.message,
            "plan": self.plan,
        }


def append_audit_log(path: str, entry: AuditLogEntry) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), sort_keys=True) + "\n")
