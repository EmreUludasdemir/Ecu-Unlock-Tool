"""
Driver kayit defteri + ECU -> driver eslemesi.

Autotuner'in "araba listesi"nin minik karsiligi: her driver kendini kaydeder,
identify sirasinda okunan SW/HW numarasina gore dogru driver secilir.
"""

from __future__ import annotations

from typing import List, Optional, Type

from .ecu_driver import ECUDriver
from .exceptions import DriverNotFoundError


class DriverRegistry:
    def __init__(self) -> None:
        self._drivers: List[Type[ECUDriver]] = []

    def register(self, driver_cls: Type[ECUDriver]) -> Type[ECUDriver]:
        """Dekorator olarak kullan: @registry.register"""
        self._drivers.append(driver_cls)
        return driver_cls

    def all(self) -> List[Type[ECUDriver]]:
        return list(self._drivers)

    def match(self, ecu_id: str) -> Type[ECUDriver]:
        """SW/HW numarasina gore driver bul."""
        for drv in self._drivers:
            for prefix in drv.supported_ids:
                if ecu_id.startswith(prefix):
                    return drv
        raise DriverNotFoundError(f"'{ecu_id}' icin kayitli driver yok.")

    def get(self, name: str) -> Optional[Type[ECUDriver]]:
        """Isimle driver getir (manuel secim icin)."""
        for drv in self._drivers:
            if drv.name == name:
                return drv
        return None


# Global registry - driver modulleri import edilince kendilerini kaydeder.
registry = DriverRegistry()
