"""AutoFlash - pluggable, cok-platformlu ECU flashing framework iskeleti."""

from .connection import (
    BaseConnection,
    IsoTpCanConnection,
    BenchConnection,
    BootConnection,
)
from .ecu_driver import ECUDriver, EcuInfo, MemoryBlock
from .flasher import Flasher
from .registry import registry
from .virtual import VirtualCanConnection, VirtualECU

__version__ = "0.2.0"

__all__ = [
    "BaseConnection",
    "IsoTpCanConnection",
    "BenchConnection",
    "BootConnection",
    "ECUDriver",
    "EcuInfo",
    "MemoryBlock",
    "Flasher",
    "registry",
    "VirtualCanConnection",
    "VirtualECU",
]
