"""
ECU driver arayuzu - Autotuner-tarzi bir tool'un KALBI.

Isin %90'i burada: her ECU ailesi (Simos18, EDC17, MG1, MEDC17, ...) icin bir
driver yazarsin. Driver, o platforma OZEL su bilgileri kapsuller:

    - seed/key algoritmasi  (UDS 0x27 SecurityAccess)
    - flash memory haritasi (hangi blok nerede)
    - container formati     (encryption + compression)
    - checksum semasi       (yazmadan once duzeltme)
    - ECU tanima (identify)

Framework (Connection + Flasher) platformdan bagimsizdir; driver'lar onu
platforma ozel kilar. Yeni ECU eklemek = yeni bir driver modulu.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class EcuInfo:
    """ECU kimlik bilgisi (identify ciktisi)."""

    name: str
    hw_number: str = ""
    sw_number: str = ""
    vin: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class MemoryBlock:
    """Flash icindeki tek bir blok (orn. CAL, ASW1, ASW2)."""

    name: str
    address: int
    size: int
    compression: str = "none"   # none | lzss | ...
    encryption: str = "none"    # none | aes-cbc | ...


class ECUDriver(ABC):
    """Tek bir ECU ailesi icin platform-spesifik mantik."""

    name: str = "generic"
    # Bu driver'in destekledigi SW/HW numara on-ekleri (identify eslemesi icin).
    supported_ids: tuple = ()

    # --- tanima -----------------------------------------------------------
    @abstractmethod
    def identify(self, client) -> EcuInfo:
        """Acik bir UDS oturumunda DID'leri okuyup ECU kimligini cikar."""
        ...

    # --- bellek haritasi --------------------------------------------------
    @abstractmethod
    def memory_map(self) -> List[MemoryBlock]:
        ...

    # --- guvenlik ---------------------------------------------------------
    @abstractmethod
    def compute_key(self, seed: bytes, level: int) -> bytes:
        """
        Seed -> key (UDS 0x27). Her OEM/platformda farklidir ve isin en kritik
        yeridir. Framework bunu SAGLAMAZ; her driver kendi platformu icin,
        sahip oldugu/uzerinde calismaya yetkili oldugu ECU'lar dahilinde doldurur.
        """
        ...

    # --- container (oku tarafı) ------------------------------------------
    @abstractmethod
    def decode_container(self, raw: bytes, block: MemoryBlock) -> bytes:
        """Okunan ham blogu cozer: decrypt -> decompress -> duz .bin."""
        ...

    # --- container (yaz tarafı) ------------------------------------------
    @abstractmethod
    def encode_container(self, data: bytes, block: MemoryBlock) -> bytes:
        """Yazim icin hazirlar: checksum-correct -> compress -> encrypt."""
        ...

    @abstractmethod
    def correct_checksum(self, data: bytes, block: MemoryBlock) -> bytes:
        """Degistirilmis blogun checksum'larini yeniden hesapla."""
        ...
