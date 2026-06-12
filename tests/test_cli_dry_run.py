from __future__ import annotations

import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from autoflash import cli
from autoflash.virtual import VirtualCanConnection, VirtualECU


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAL_ADDR = 0x80000000


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "autoflash.cli", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def prepare_dump(tmp_path: Path) -> Path:
    out_dir = tmp_path / "dump"
    result = run_cli("read", "--virtual", "--out", str(out_dir))
    assert_success(result)
    return out_dir


def test_cli_write_plan_virtual(tmp_path: Path) -> None:
    out_dir = prepare_dump(tmp_path)

    result = run_cli(
        "write",
        "--virtual",
        "--block",
        "CAL",
        "--file",
        str(out_dir / "CAL.bin"),
        "--plan",
    )

    assert_success(result)
    assert "operation: write" in result.stdout
    assert "driver: mock" in result.stdout
    assert "block: CAL" in result.stdout
    assert "address: 0x80000000" in result.stdout


def test_cli_write_dry_run_virtual(tmp_path: Path) -> None:
    out_dir = prepare_dump(tmp_path)

    result = run_cli(
        "write",
        "--virtual",
        "--block",
        "CAL",
        "--file",
        str(out_dir / "CAL.bin"),
        "--dry-run",
    )

    assert_success(result)
    assert "dry-run" in result.stdout
    assert "write islemi calistirilmadi" in result.stdout


def test_cli_dry_run_does_not_modify_virtual_ecu_memory(monkeypatch, tmp_path: Path) -> None:
    ecu = VirtualECU()
    original = ecu.decoded_block(CAL_ADDR)
    modified = bytearray(original)
    modified[10] ^= 0xFF
    source = tmp_path / "CAL_modified.bin"
    source.write_bytes(modified)

    monkeypatch.setattr(cli, "_connection", lambda args: VirtualCanConnection(ecu))
    args = SimpleNamespace(
        virtual=True,
        block="CAL",
        file=str(source),
        dry_run=True,
        plan=False,
        audit_log=None,
    )

    assert cli.cmd_write(args) == 0
    assert ecu.decoded_block(CAL_ADDR) == original


def test_cli_write_dry_run_audit_log(tmp_path: Path) -> None:
    out_dir = prepare_dump(tmp_path)
    audit_path = tmp_path / "logs" / "audit.jsonl"

    result = run_cli(
        "write",
        "--virtual",
        "--block",
        "CAL",
        "--file",
        str(out_dir / "CAL.bin"),
        "--dry-run",
        "--audit-log",
        str(audit_path),
    )

    assert_success(result)
    assert audit_path.is_file()
    rows = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert rows[-1]["operation_type"] == "write"
    assert rows[-1]["success"] is True
    assert rows[-1]["dry_run"] is True
    assert rows[-1]["plan"]["blocks"][0]["block_name"] == "CAL"


def test_cli_write_virtual_still_executes(tmp_path: Path) -> None:
    out_dir = prepare_dump(tmp_path)

    result = run_cli(
        "write",
        "--virtual",
        "--block",
        "CAL",
        "--file",
        str(out_dir / "CAL.bin"),
    )

    assert_success(result)
    assert "flash tamam" in result.stdout
    assert "CAL" in result.stdout
