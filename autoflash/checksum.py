"""Checksum strategy abstractions for safe lab workflows."""

from __future__ import annotations

import struct
import zlib
from abc import ABC, abstractmethod


class ChecksumError(ValueError):
    """Raised when checksum input cannot be handled safely."""


class ChecksumStrategy(ABC):
    """Base interface for checksum strategies."""

    name: str = "base"

    @abstractmethod
    def apply(self, data: bytes) -> bytes:
        """Return data with checksum bytes updated."""
        ...

    @abstractmethod
    def verify(self, data: bytes) -> bool:
        """Return True when checksum bytes match payload bytes."""
        ...


class ToyCrc32Checksum(ChecksumStrategy):
    """
    Toy CRC32 checksum used by VirtualECU and MockDriver tests.

    The last four bytes are treated as the checksum field. The checksum is
    little-endian CRC32 of all preceding bytes. This is simulator-only lab logic,
    not an OEM checksum implementation.
    """

    name = "toy-crc32-last4"

    def apply(self, data: bytes) -> bytes:
        if len(data) < 4:
            raise ChecksumError("ToyCrc32Checksum requires at least 4 bytes.")
        payload = data[:-4]
        checksum = struct.pack("<I", zlib.crc32(payload) & 0xFFFF_FFFF)
        return payload + checksum

    def verify(self, data: bytes) -> bool:
        if len(data) < 4:
            return False
        payload = data[:-4]
        expected = struct.pack("<I", zlib.crc32(payload) & 0xFFFF_FFFF)
        return data[-4:] == expected
