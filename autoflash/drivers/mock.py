"""
Mock driver - sanal ECU ile eslesir (Asama 2).

Gercek Simos18 driver'inin yerini tutar: ayni metot yapisini doldurur ama
platform-spesifik algoritmalar yerine VirtualECU ile paylasilan "toy"
fonksiyonlari kullanir. Boylece tum pipeline (identify/read/write/security/
checksum) uctan uca calisir ve test edilebilir.

Gercek bir ECU'ya gecerken yapacagin tek sey: bu metotlari o ECU'nun gercek
algoritmalariyla degistirmek. Cagri yapisi ayni kalir.
"""

from __future__ import annotations

from typing import List

from ..checksum import ToyCrc32Checksum
from ..container import ToyXorContainerCodec
from ..ecu_driver import ECUDriver, EcuInfo, MemoryBlock
from ..registry import registry
from ..security import MockXorRotateSeedKeyProvider


@registry.register
class MockDriver(ECUDriver):
    name = "mock"
    supported_ids = ("MOCK",)

    def __init__(self) -> None:
        self.seed_key_provider = MockXorRotateSeedKeyProvider()
        self.checksum_strategy = ToyCrc32Checksum()
        self.container_codec = ToyXorContainerCodec()

    def identify(self, client) -> EcuInfo:
        info = EcuInfo(name="VirtualECU")
        try:
            resp = client.read_data_by_identifier(0xF190)  # VIN
            info.vin = str(resp.service_data.values[0xF190]).strip()
        except Exception:
            pass
        try:
            resp = client.read_data_by_identifier(0xF188)  # SW number
            info.sw_number = str(resp.service_data.values[0xF188]).strip()
        except Exception:
            pass
        return info

    def memory_map(self) -> List[MemoryBlock]:
        return [
            MemoryBlock("CAL", address=0x80000000, size=256),
            MemoryBlock("ASW", address=0x80100000, size=256),
        ]

    def compute_key(self, seed: bytes, level: int) -> bytes:
        return self.seed_key_provider.compute_key(seed, level)

    def decode_container(self, raw: bytes, block: MemoryBlock) -> bytes:
        # decrypt (toy). Gercekte: AES-CBC decrypt + LZSS decompress.
        return self.container_codec.decode(raw)

    def encode_container(self, data: bytes, block: MemoryBlock) -> bytes:
        # checksum-correct -> encrypt. Gercekte: + compress.
        return self.container_codec.encode(self.correct_checksum(data, block))

    def correct_checksum(self, data: bytes, block: MemoryBlock) -> bytes:
        return self.checksum_strategy.apply(data)
