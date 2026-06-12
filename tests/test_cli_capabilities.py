from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_capabilities_virtual() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "autoflash.cli", "capabilities", "--virtual"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    output = result.stdout
    assert "driver: mock" in output
    assert "safety_level: virtual_only" in output
    assert "connection_modes: virtual" in output
    assert "real_ecu_supported: false" in output
    assert "allows_write: false" in output
