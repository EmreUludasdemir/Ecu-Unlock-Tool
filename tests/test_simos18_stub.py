from __future__ import annotations

import pytest

from autoflash.drivers.simos18 import Simos18Driver


def test_simos18_driver_metadata() -> None:
    driver = Simos18Driver()

    assert driver.name == "simos18"
    assert driver.supported_ids


def test_simos18_memory_map_has_readonly_placeholders() -> None:
    driver = Simos18Driver()
    blocks = driver.memory_map()
    names = {block.name for block in blocks}

    assert blocks
    assert {"CAL", "ASW1"} & names


def test_simos18_security_access_intentionally_disabled() -> None:
    driver = Simos18Driver()

    with pytest.raises(NotImplementedError, match="read-only research branch"):
        driver.compute_key(b"\x01\x02\x03\x04", level=1)


def test_simos18_container_decode_intentionally_disabled() -> None:
    driver = Simos18Driver()
    block = driver.memory_map()[0]

    with pytest.raises(NotImplementedError, match="no bypass/exploit"):
        driver.decode_container(b"raw", block)


def test_simos18_write_pipeline_intentionally_disabled() -> None:
    driver = Simos18Driver()
    block = driver.memory_map()[0]

    with pytest.raises(NotImplementedError, match="write support"):
        driver.encode_container(b"flat", block)
    with pytest.raises(NotImplementedError, match="write-enabling"):
        driver.correct_checksum(b"flat", block)
