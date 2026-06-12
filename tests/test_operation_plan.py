from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoflash.drivers.mock import MockDriver
from autoflash.operation_plan import (
    AuditLogEntry,
    OperationPlanError,
    OperationPlanner,
    OperationType,
    append_audit_log,
)
from autoflash.virtual import VirtualCanConnection, VirtualECU


def test_operation_planner_builds_mock_cal_write_plan(tmp_path: Path) -> None:
    file_path = tmp_path / "CAL.bin"
    file_path.write_bytes(b"\x00" * 256)

    plan = OperationPlanner().plan_write(
        driver=MockDriver(),
        connection=VirtualCanConnection(VirtualECU()),
        files={"CAL": str(file_path)},
        dry_run=True,
    )

    assert plan.operation_type == OperationType.WRITE
    assert plan.driver_name == "mock"
    assert plan.connection_mode == "virtual"
    assert plan.safety_level == "virtual_only"
    assert plan.dry_run is True
    assert plan.blocks[0].block_name == "CAL"
    assert plan.blocks[0].address == 0x80000000
    assert plan.blocks[0].expected_size == 256
    assert plan.blocks[0].file_size == 256


def test_operation_planner_rejects_unknown_block(tmp_path: Path) -> None:
    file_path = tmp_path / "UNKNOWN.bin"
    file_path.write_bytes(b"\x00" * 16)

    with pytest.raises(OperationPlanError, match="Unknown memory block"):
        OperationPlanner().plan_write(
            driver=MockDriver(),
            connection=VirtualCanConnection(VirtualECU()),
            files={"UNKNOWN": str(file_path)},
            dry_run=True,
        )


def test_operation_planner_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(OperationPlanError, match="File not found"):
        OperationPlanner().plan_write(
            driver=MockDriver(),
            connection=VirtualCanConnection(VirtualECU()),
            files={"CAL": str(tmp_path / "missing.bin")},
            dry_run=True,
        )


def test_operation_plan_to_dict_is_json_serializable(tmp_path: Path) -> None:
    file_path = tmp_path / "CAL.bin"
    file_path.write_bytes(b"\x00" * 256)
    plan = OperationPlanner().plan_write(
        driver=MockDriver(),
        connection=VirtualCanConnection(VirtualECU()),
        files={"CAL": str(file_path)},
        dry_run=True,
    )

    encoded = json.dumps(plan.to_dict())

    assert '"operation_type": "write"' in encoded


def test_operation_plan_to_text_is_readable(tmp_path: Path) -> None:
    file_path = tmp_path / "CAL.bin"
    file_path.write_bytes(b"\x00" * 256)
    plan = OperationPlanner().plan_write(
        driver=MockDriver(),
        connection=VirtualCanConnection(VirtualECU()),
        files={"CAL": str(file_path)},
        dry_run=True,
    )

    text = plan.to_text()

    assert "operation: write" in text
    assert "driver: mock" in text
    assert "address: 0x80000000" in text


def test_append_audit_log_writes_jsonl(tmp_path: Path) -> None:
    file_path = tmp_path / "CAL.bin"
    file_path.write_bytes(b"\x00" * 256)
    plan = OperationPlanner().plan_write(
        driver=MockDriver(),
        connection=VirtualCanConnection(VirtualECU()),
        files={"CAL": str(file_path)},
        dry_run=True,
    )
    entry = AuditLogEntry.from_plan(plan, True, "dry-run completed")
    audit_path = tmp_path / "logs" / "audit.jsonl"

    append_audit_log(str(audit_path), entry)

    rows = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert rows[0]["operation_type"] == "write"
    assert rows[0]["success"] is True
    assert rows[0]["plan"]["blocks"][0]["block_name"] == "CAL"
