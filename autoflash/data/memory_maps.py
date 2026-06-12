"""Default memory map metadata.

The entries in this module are safe lab metadata and read-only placeholders.
They are not an unlock, bypass, pinout, recovery, or write-support database.
"""

from __future__ import annotations

from ..memory_map import EcuFamilySpec, MemoryBlockSpec, MemoryMapDatabase


def build_default_memory_map_database() -> MemoryMapDatabase:
    db = MemoryMapDatabase()
    db.register(
        EcuFamilySpec(
            family="mock",
            display_name="Virtual Mock ECU",
            supported_ids=("MOCK",),
            blocks=(
                MemoryBlockSpec(
                    "CAL",
                    address=0x80000000,
                    size=256,
                    description="Virtual calibration block",
                ),
                MemoryBlockSpec(
                    "ASW",
                    address=0x80100000,
                    size=256,
                    description="Virtual application software block",
                ),
            ),
            notes="Toy metadata for VirtualECU and MockDriver tests.",
        )
    )
    db.register(
        EcuFamilySpec(
            family="simos18",
            display_name="Simos18 Read-Only Placeholder",
            supported_ids=("5G0906259", "8V0906259", "06K906259"),
            blocks=(
                MemoryBlockSpec(
                    "CAL",
                    address=0x0080_0000,
                    size=0x10_0000,
                    description="Placeholder calibration block metadata",
                    compression="lzss",
                    encryption="aes-cbc",
                ),
                MemoryBlockSpec(
                    "ASW1",
                    address=0x0090_0000,
                    size=0x20_0000,
                    description="Placeholder application software block metadata",
                    compression="lzss",
                    encryption="aes-cbc",
                ),
            ),
            notes=(
                "Placeholder only; read-only research metadata; no unlock, "
                "bypass, write, recovery, or real ECU support."
            ),
        )
    )
    return db
