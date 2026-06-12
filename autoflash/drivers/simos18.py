"""
Simos18 driver - read-only research stub.

This driver documents how a future Simos18 integration could fit the AutoFlash
driver interface. It is intentionally limited to identification and placeholder
metadata. SecurityAccess, protected container handling, checksum correction, and
real write support are not implemented in this branch.

References are kept for public documentation context only:

    bri3d/VW_Flash
    bri3d/Simos18_SBOOT

No unlock, bypass, exploit, boot password recovery, or emissions defeat logic is
provided here.
"""

from __future__ import annotations

from typing import List

from ..ecu_driver import ECUDriver, EcuInfo, MemoryBlock
from ..registry import registry


@registry.register
class Simos18Driver(ECUDriver):
    name = "simos18"
    # Illustrative VW/Audi 2.0 TFSI SW prefixes. This is not a complete list.
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
        # Placeholder metadata only. Real addresses and sizes vary by ECU
        # revision and must be validated separately before any read-only use.
        return [
            MemoryBlock("CAL",  address=0x0080_0000, size=0x10_0000,
                        compression="lzss", encryption="aes-cbc"),
            MemoryBlock("ASW1", address=0x0090_0000, size=0x20_0000,
                        compression="lzss", encryption="aes-cbc"),
        ]

    def compute_key(self, seed: bytes, level: int) -> bytes:
        raise NotImplementedError(
            "Simos18 SecurityAccess is intentionally not implemented in this "
            "read-only research branch. No unlock, bypass, or exploit logic is "
            "provided."
        )

    def decode_container(self, raw: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "Simos18 protected container decoding is not implemented in this "
            "read-only branch. This stub provides no bypass/exploit "
            "implementation."
        )

    def encode_container(self, data: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "Simos18 container encoding is intentionally disabled in this "
            "read-only branch. No real ECU write support is provided."
        )

    def correct_checksum(self, data: bytes, block: MemoryBlock) -> bytes:
        raise NotImplementedError(
            "Simos18 checksum correction is intentionally not implemented in "
            "this read-only branch. No write-enabling logic is provided."
        )
