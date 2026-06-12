"""Driver capability and safety metadata."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class DriverCapabilityError(ValueError):
    """Raised when driver capability metadata is invalid."""


class ConnectionMode(str, Enum):
    VIRTUAL = "virtual"
    OBD = "obd"
    BENCH = "bench"
    BOOT = "boot"


class DriverSafetyLevel(str, Enum):
    VIRTUAL_ONLY = "virtual_only"
    READ_ONLY = "read_only"
    RESEARCH_STUB = "research_stub"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class DriverCapabilities:
    driver_name: str
    safety_level: DriverSafetyLevel
    supported_connection_modes: Tuple[ConnectionMode, ...] = (ConnectionMode.VIRTUAL,)
    identify_supported: bool = True
    read_supported: bool = False
    write_supported: bool = False
    security_access_supported: bool = False
    real_ecu_supported: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.driver_name:
            raise DriverCapabilityError("driver_name must not be empty.")
        if not self.supported_connection_modes:
            raise DriverCapabilityError(
                "supported_connection_modes must not be empty."
            )

    def allows_write(self) -> bool:
        return self.write_supported and self.real_ecu_supported

    def requires_virtual(self) -> bool:
        return self.supported_connection_modes == (ConnectionMode.VIRTUAL,)
