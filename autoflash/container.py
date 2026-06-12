"""Container codec abstractions for safe lab workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod


DEFAULT_TOY_XOR_KEY = b"\xDE\xAD\xBE\xEF"


class ContainerCodecError(ValueError):
    """Raised when a container codec cannot safely process input."""


class ContainerCodec(ABC):
    """Base interface for container codecs."""

    name: str = "base"

    @abstractmethod
    def encode(self, flat: bytes) -> bytes:
        """Convert flat bytes to a container payload."""
        ...

    @abstractmethod
    def decode(self, encoded: bytes) -> bytes:
        """Convert a container payload to flat bytes."""
        ...


class ToyXorContainerCodec(ContainerCodec):
    """
    Toy XOR codec used by VirtualECU and MockDriver tests.

    This is a reversible simulator transform, not real ECU encryption,
    compression, signing, or protection bypass logic.
    """

    name = "toy-xor"

    def __init__(self, key: bytes = DEFAULT_TOY_XOR_KEY) -> None:
        if not key:
            raise ContainerCodecError("ToyXorContainerCodec key must not be empty.")
        self.key = key

    def encode(self, flat: bytes) -> bytes:
        return self._xor(flat)

    def decode(self, encoded: bytes) -> bytes:
        return self._xor(encoded)

    def _xor(self, data: bytes) -> bytes:
        return bytes(b ^ self.key[i % len(self.key)] for i, b in enumerate(data))
