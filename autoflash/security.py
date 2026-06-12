"""
Seed-key provider abstractions for safe lab and simulator workflows.

This module does not contain real OEM seed-key algorithms, unlock bypasses, or
exploit logic. Providers are explicit dependencies so production drivers can
fail closed unless a safe, authorized implementation is supplied.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


MOCK_XOR_ROTATE_SECRET = 0x1234_5678


class SecurityProviderError(RuntimeError):
    """Raised when a seed-key provider cannot safely produce a key."""


class SeedKeyProvider(ABC):
    """Base interface for seed-key providers."""

    name: str = "base"

    @abstractmethod
    def compute_key(self, seed: bytes, level: int) -> bytes:
        """Return a key for a seed and security level."""
        ...


class NoSeedKeyProvider(SeedKeyProvider):
    """Fail-closed provider for drivers without authorized seed-key support."""

    name = "none"

    def compute_key(self, seed: bytes, level: int) -> bytes:
        raise SecurityProviderError(
            "No seed-key provider is configured. This project does not include "
            "real OEM seed-key algorithms, unlock bypasses, or exploit logic."
        )


class MockXorRotateSeedKeyProvider(SeedKeyProvider):
    """
    Toy provider used only by VirtualECU and MockDriver tests.

    The algorithm is a deterministic XOR-and-rotate transform shared with the
    simulator. It is not a real ECU seed-key algorithm and must not be treated
    as an unlock or bypass implementation.
    """

    name = "mock-xor-rotate"

    def __init__(self, secret: int = MOCK_XOR_ROTATE_SECRET) -> None:
        self.secret = secret

    def compute_key(self, seed: bytes, level: int) -> bytes:
        if not seed:
            raise SecurityProviderError("Seed must not be empty.")
        val = int.from_bytes(seed, "big")
        mixed = (val ^ self.secret) & 0xFFFF_FFFF
        rotated = ((mixed << 3) | (mixed >> 29)) & 0xFFFF_FFFF
        return rotated.to_bytes(4, "big")


class SeedKeyProviderRegistry:
    """Small in-memory registry for named seed-key providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, SeedKeyProvider] = {}

    def register(self, provider: SeedKeyProvider) -> SeedKeyProvider:
        if not provider.name:
            raise SecurityProviderError("Seed-key provider name must not be empty.")
        self._providers[provider.name] = provider
        return provider

    def get(self, name: str) -> SeedKeyProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise SecurityProviderError(f"Seed-key provider not found: {name}") from exc

    def all(self) -> List[SeedKeyProvider]:
        return list(self._providers.values())


default_seed_key_registry = SeedKeyProviderRegistry()
default_seed_key_registry.register(NoSeedKeyProvider())
default_seed_key_registry.register(MockXorRotateSeedKeyProvider())
