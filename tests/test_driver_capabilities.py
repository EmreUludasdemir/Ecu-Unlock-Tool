from __future__ import annotations

import pytest

from autoflash.capabilities import ConnectionMode, DriverSafetyLevel
from autoflash.drivers.mock import MockDriver
from autoflash.drivers.simos18 import Simos18Driver
from autoflash.ecu_driver import ECUDriver, EcuInfo, MemoryBlock


def test_mock_driver_capabilities_are_virtual_only() -> None:
    caps = MockDriver().capabilities()

    assert caps.driver_name == "mock"
    assert caps.safety_level == DriverSafetyLevel.VIRTUAL_ONLY
    assert caps.supported_connection_modes == (ConnectionMode.VIRTUAL,)
    assert caps.requires_virtual() is True


def test_mock_driver_virtual_write_is_not_real_ecu_write() -> None:
    caps = MockDriver().capabilities()

    assert caps.read_supported is True
    assert caps.write_supported is True
    assert caps.security_access_supported is True
    assert caps.real_ecu_supported is False
    assert caps.allows_write() is False


def test_simos18_driver_capabilities_are_read_only_stub() -> None:
    caps = Simos18Driver().capabilities()

    assert caps.driver_name == "simos18"
    assert caps.safety_level == DriverSafetyLevel.READ_ONLY
    assert caps.supported_connection_modes == (ConnectionMode.OBD,)
    assert caps.identify_supported is True
    assert caps.write_supported is False
    assert caps.security_access_supported is False
    assert caps.real_ecu_supported is False
    assert caps.allows_write() is False


def test_simos18_dangerous_methods_still_raise() -> None:
    driver = Simos18Driver()
    block = driver.memory_map()[0]

    with pytest.raises(NotImplementedError):
        driver.compute_key(b"\x01\x02\x03\x04", level=1)
    with pytest.raises(NotImplementedError):
        driver.decode_container(b"raw", block)
    with pytest.raises(NotImplementedError):
        driver.encode_container(b"flat", block)
    with pytest.raises(NotImplementedError):
        driver.correct_checksum(b"flat", block)


def test_default_ecu_driver_capabilities_are_fail_closed() -> None:
    class MinimalDriver(ECUDriver):
        name = "minimal"

        def identify(self, client) -> EcuInfo:
            return EcuInfo(name="minimal")

        def memory_map(self) -> list[MemoryBlock]:
            return []

        def compute_key(self, seed: bytes, level: int) -> bytes:
            raise NotImplementedError

        def decode_container(self, raw: bytes, block: MemoryBlock) -> bytes:
            raise NotImplementedError

        def encode_container(self, data: bytes, block: MemoryBlock) -> bytes:
            raise NotImplementedError

        def correct_checksum(self, data: bytes, block: MemoryBlock) -> bytes:
            raise NotImplementedError

    caps = MinimalDriver().capabilities()

    assert caps.driver_name == "minimal"
    assert caps.safety_level == DriverSafetyLevel.RESEARCH_STUB
    assert caps.read_supported is False
    assert caps.write_supported is False
    assert caps.real_ecu_supported is False
    assert caps.allows_write() is False
