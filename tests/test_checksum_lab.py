from __future__ import annotations

import pytest

from autoflash.checksum import ChecksumError, ToyCrc32Checksum
from autoflash.virtual import apply_checksum, verify_checksum


def test_toy_crc32_checksum_apply_then_verify() -> None:
    strategy = ToyCrc32Checksum()
    data = b"calibration-payload" + b"\x00\x00\x00\x00"

    checked = strategy.apply(data)

    assert strategy.verify(checked) is True
    assert checked == apply_checksum(data)
    assert verify_checksum(checked) is True


def test_toy_crc32_checksum_detects_corruption() -> None:
    strategy = ToyCrc32Checksum()
    checked = bytearray(strategy.apply(b"payload" + b"\x00\x00\x00\x00"))

    checked[1] ^= 0xFF

    assert strategy.verify(bytes(checked)) is False


def test_toy_crc32_checksum_handles_short_data_safely() -> None:
    strategy = ToyCrc32Checksum()

    with pytest.raises(ChecksumError, match="at least 4 bytes"):
        strategy.apply(b"\x00\x01\x02")
    assert strategy.verify(b"\x00\x01\x02") is False
