"""
Simos18 driver - ORNEK / ISKELET.

Bu, framework'un nasil bir platforma baglandigini gosteren bir sablon. Simos18
secildi cunku tum detaylari ACIK KAYNAK ve dokumante:

    bri3d/VW_Flash         -> flashing toolchain, checksum, encryption, compression
    bri3d/Simos18_SBOOT    -> SBOOT / seed-key / boot password dokumantasyonu
    bri3d/TC1791_CAN_BSL   -> Tricore BSL (boot modu)

Platform-spesifik algoritmalar (seed/key, AES-CBC "Encryption A", LZSS
"Compression A", checksum) burada KASTEN implemente edilmedi. Kendi sahip
oldugun ECU icin yukaridaki acik kaynak projeleri referans alarak doldurursun.
"""

from __future__ import annotations

from typing import List

from ..data.memory_maps import build_default_memory_map_database
from ..ecu_driver import ECUDriver, EcuInfo, MemoryBlock
from ..memory_map import MemoryBlockSpec
from ..registry import registry


@registry.register
class Simos18Driver(ECUDriver):
    name = "simos18"
    # Ornek VW/Audi 2.0 TFSI SW on-ekleri (illustratif - gercek liste cok daha genis).
    supported_ids = ("5G0906259", "8V0906259", "06K906259")

    def identify(self, client) -> EcuInfo:
        from udsoncan import DataIdentifier

        info = EcuInfo(name="Simos18")
        try:
            vin = client.read_data_by_identifier(DataIdentifier.VIN)
            info.vin = bytes(
                vin.service_data.values[DataIdentifier.VIN]
            ).decode("ascii", "ignore").strip()
        except Exception:
            pass
        return info

    def memory_map(self) -> List[MemoryBlock]:
        # Placeholder metadata only. This is not write-ready real ECU support.
        spec = build_default_memory_map_database().get("simos18")
        return [_to_memory_block(block) for block in spec.blocks]

    def compute_key(self, seed: bytes, level: int) -> bytes:
        raise NotImplementedError(
            "Simos18 SecurityAccess platform-spesifik. Sahip oldugun ECU icin "
            "bri3d/VW_Flash + Simos18_SBOOT referansiyla implemente et."
        )

    def decode_container(self, raw: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "Encryption A (fixed-key AES-CBC) + Compression A (LZSS) cozumu icin "
            "VW_Flash/lib/modules/simos18.py'a bak."
        )

    def encode_container(self, data: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "Simos18 encode/write support is intentionally not implemented."
        )

    def correct_checksum(self, data: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "ASW/CAL ve ECM2->ECM3 checksum duzeltmesi icin VW_Flash referans."
        )


def _to_memory_block(spec: MemoryBlockSpec) -> MemoryBlock:
    return MemoryBlock(
        name=spec.name,
        address=spec.address,
        size=spec.size,
        compression=spec.compression,
        encryption=spec.encryption,
    )
