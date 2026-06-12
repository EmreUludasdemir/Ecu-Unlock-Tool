from __future__ import annotations

from pathlib import Path

import pytest
from udsoncan.exceptions import NegativeResponseException

from autoflash import Flasher
from autoflash.drivers import mock  # noqa: F401  (register mock driver)
from autoflash.virtual import VirtualCanConnection, VirtualECU


CAL_ADDR = 0x80000000


def test_bad_checksum_does_not_modify_ecu_memory(tmp_path: Path) -> None:
    ecu = VirtualECU()
    flasher = Flasher(VirtualCanConnection(ecu))

    flasher.identify()
    flasher.read(out_dir=str(tmp_path))
    original_cal = ecu.decoded_block(CAL_ADDR)

    flasher.driver.correct_checksum = lambda data, block: data
    bad = bytearray((tmp_path / "CAL.bin").read_bytes())
    bad[-1] ^= 0xAA
    bad_path = tmp_path / "CAL_bad.bin"
    bad_path.write_bytes(bad)

    with pytest.raises(NegativeResponseException):
        flasher.write(files={"CAL": str(bad_path)})

    assert ecu.decoded_block(CAL_ADDR) == original_cal
