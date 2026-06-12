from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str, cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "autoflash.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_cli_identify_virtual() -> None:
    result = run_cli("identify", "--virtual")

    assert_success(result)
    output = result.stdout
    assert "VirtualECU" in output
    assert "WVWMOCK1234567890" in output
    assert "MOCK0001" in output
    assert "Driver: mock" in output


def test_cli_read_virtual(tmp_path: Path) -> None:
    out_dir = tmp_path / "dump"
    result = run_cli("read", "--virtual", "--out", str(out_dir))

    assert_success(result)
    assert (out_dir / "CAL.bin").is_file()
    assert (out_dir / "ASW.bin").is_file()
    assert "CAL.bin" in result.stdout
    assert "ASW.bin" in result.stdout


def test_cli_write_virtual(tmp_path: Path) -> None:
    out_dir = tmp_path / "dump"
    read_result = run_cli("read", "--virtual", "--out", str(out_dir))
    assert_success(read_result)

    write_result = run_cli(
        "write",
        "--virtual",
        "--block",
        "CAL",
        "--file",
        str(out_dir / "CAL.bin"),
    )

    assert_success(write_result)
    assert "flash tamam" in write_result.stdout
    assert "CAL" in write_result.stdout
