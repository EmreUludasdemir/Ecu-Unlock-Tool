from __future__ import annotations

import pytest

from autoflash.drivers.mock import MockDriver
from autoflash.security import (
    MockXorRotateSeedKeyProvider,
    NoSeedKeyProvider,
    SecurityProviderError,
    SeedKeyProviderRegistry,
)
from autoflash.virtual import seed_to_key


def test_mock_seed_key_provider_is_deterministic() -> None:
    provider = MockXorRotateSeedKeyProvider()
    seed = b"\x01\x02\x03\x04"

    assert provider.compute_key(seed, level=1) == provider.compute_key(seed, level=1)


def test_mock_seed_key_provider_varies_by_seed() -> None:
    provider = MockXorRotateSeedKeyProvider()

    assert provider.compute_key(b"\x01\x02\x03\x04", level=1) != provider.compute_key(
        b"\x01\x02\x03\x05", level=1
    )


def test_mock_seed_key_provider_matches_virtual_ecu_toy_algorithm() -> None:
    provider = MockXorRotateSeedKeyProvider()
    seed = b"\x10\x20\x30\x40"

    assert provider.compute_key(seed, level=1) == seed_to_key(seed)


def test_no_seed_key_provider_fails_closed() -> None:
    provider = NoSeedKeyProvider()

    with pytest.raises(SecurityProviderError, match="does not include real OEM"):
        provider.compute_key(b"\x01\x02\x03\x04", level=1)


def test_seed_key_provider_registry_registers_and_finds_provider() -> None:
    registry = SeedKeyProviderRegistry()
    provider = MockXorRotateSeedKeyProvider()

    registry.register(provider)

    assert registry.get("mock-xor-rotate") is provider
    assert registry.all() == [provider]


def test_mock_driver_compute_key_uses_provider() -> None:
    class FixedProvider:
        name = "fixed"

        def __init__(self) -> None:
            self.calls = []

        def compute_key(self, seed: bytes, level: int) -> bytes:
            self.calls.append((seed, level))
            return b"\xAA\xBB\xCC\xDD"

    provider = FixedProvider()
    driver = MockDriver()
    driver.seed_key_provider = provider

    assert driver.compute_key(b"\x01\x02\x03\x04", level=3) == b"\xAA\xBB\xCC\xDD"
    assert provider.calls == [(b"\x01\x02\x03\x04", 3)]
