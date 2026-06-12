"""
Flasher - orkestrasyon katmani (Autotuner'in "core"u).

Akis:
    connect -> identify -> driver sec -> read / write pipeline

read:
    programming/extended session -> her blogu UDS ile oku -> decode_container -> .bin kaydet

write:
    programming session -> SecurityAccess (driver.compute_key)
    -> her blok icin: encode_container -> RequestDownload(0x34)
       -> tekrarli TransferData(0x36) -> RequestTransferExit(0x37)

Not: Gercek read primitive'i ECU'ya gore degisir (ReadMemoryByAddress 0x23,
upload 0x35, ya da uretici-spesifik routine). Burada iskelet/akis verilmistir;
blok-seviyesi okuma driver/ECU'ya gore baglanir.
"""

from __future__ import annotations

import os
from typing import List, Optional, Type

from .connection import BaseConnection
from .ecu_driver import ECUDriver, EcuInfo, MemoryBlock
from .exceptions import IdentificationError, SecurityAccessError
from .registry import registry as default_registry

# ECU SW-number DID (ISO 14229 - VehicleManufacturerECUSoftwareNumber).
DID_SW_NUMBER = 0xF188
DID_VIN = 0xF190


class Flasher:
    def __init__(
        self,
        connection: BaseConnection,
        driver: Optional[ECUDriver] = None,
        registry=default_registry,
    ) -> None:
        self.connection = connection
        self.driver = driver
        self.registry = registry
        self._info: Optional[EcuInfo] = None

    # --- udsoncan client --------------------------------------------------
    def _client(self):
        try:
            import udsoncan
            from udsoncan.client import Client
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("pip install udsoncan") from e
        config = dict(udsoncan.configs.default_client_config)
        config["data_identifiers"] = {
            DID_VIN: udsoncan.AsciiCodec(17),       # VIN
            DID_SW_NUMBER: udsoncan.AsciiCodec(8),  # ECU SW number
        }
        config["request_timeout"] = 3
        return Client(self.connection.uds_connection(), config=config)

    # --- tanima -----------------------------------------------------------
    def identify(self) -> EcuInfo:
        """ECU'yu tani ve (driver verilmediyse) uygun driver'i sec."""
        with self._client() as client:
            from udsoncan.services import DiagnosticSessionControl

            client.change_session(
                DiagnosticSessionControl.Session.extendedDiagnosticSession
            )

            if self.driver is None:
                # Once herhangi bir driver'la kimligi okumayi dene, sonra esle.
                # Pratikte once standart DID 0xF1A2/0xF187 (SW number) okunur.
                probe_id = self._read_sw_number(client)
                drv_cls: Type[ECUDriver] = self.registry.match(probe_id)
                self.driver = drv_cls()

            self._info = self.driver.identify(client)
        if self._info is None:
            raise IdentificationError("identify() bos dondu.")
        return self._info

    def _read_sw_number(self, client) -> str:
        """Standart SW-number DID'ini (0xF188) oku."""
        try:
            resp = client.read_data_by_identifier(DID_SW_NUMBER)
            return str(resp.service_data.values[DID_SW_NUMBER]).strip()
        except Exception:
            return ""

    # --- okuma ------------------------------------------------------------
    def read(self, out_dir: str, block_name: Optional[str] = None) -> List[str]:
        """ECU'dan blok(lari) oku, coz ve .bin olarak kaydet."""
        self._require_driver()
        os.makedirs(out_dir, exist_ok=True)
        blocks = self._select_blocks(block_name)
        written: List[str] = []

        with self._client() as client:
            self._enter_programming(client)
            for blk in blocks:
                raw = self._read_block_raw(client, blk)
                flat = self.driver.decode_container(raw, blk)
                path = os.path.join(out_dir, f"{blk.name}.bin")
                with open(path, "wb") as f:
                    f.write(flat)
                written.append(path)
        return written

    def _read_block_raw(self, client, blk: MemoryBlock) -> bytes:
        """
        Blogu ham (sifreli/sikistirilmis) olarak oku: UDS RequestUpload(0x35)
        -> tekrarli TransferData(0x36) -> RequestTransferExit(0x37).

        Bu, write tarafinin (0x34/0x36/0x37) simetrigidir ve cogu ECU'da gecerli
        bir okuma yontemidir. ReadMemoryByAddress(0x23) isteyen ECU'larda driver
        bu metodu override edebilir.
        """
        from udsoncan import MemoryLocation

        loc = MemoryLocation(
            address=blk.address, memorysize=blk.size,
            address_format=32, memorysize_format=32,
        )
        client.request_upload(loc)
        data = bytearray()
        seq = 1
        while len(data) < blk.size:
            resp = client.transfer_data(seq & 0xFF)
            chunk = bytes(resp.service_data.parameter_records)
            if not chunk:
                break
            data.extend(chunk)
            seq += 1
        client.request_transfer_exit()
        return bytes(data[: blk.size])

    # --- yazma ------------------------------------------------------------
    def write(self, files: dict, security_level: int = 1) -> None:
        """
        files: {block_name: path-to-flat-bin}
        Her blok: encode (checksum+compress+encrypt) -> download -> transfer -> exit.
        """
        self._require_driver()
        with self._client() as client:
            self._enter_programming(client)
            self._security_access(client, security_level)
            for name, path in files.items():
                blk = self._block_by_name(name)
                with open(path, "rb") as f:
                    flat = f.read()
                payload = self.driver.encode_container(flat, blk)
                self._download_block(client, blk, payload)

    def _security_access(self, client, level: int) -> None:
        """UDS 0x27: seed iste -> driver.compute_key -> key gonder."""
        from udsoncan.services import SecurityAccess

        try:
            seed_resp = client.request_seed(level)
            seed = bytes(seed_resp.service_data.seed)
            if not any(seed):  # ECU zaten unlocked
                return
            key = self.driver.compute_key(seed, level)
            client.send_key(level + 1, key)
        except NotImplementedError:
            raise SecurityAccessError(
                f"{self.driver.name}: compute_key() implemente edilmemis - "
                "bu platform icin seed/key gerekiyor."
            )

    def _download_block(self, client, blk: MemoryBlock, payload: bytes) -> None:
        from udsoncan import MemoryLocation

        loc = MemoryLocation(address=blk.address, memorysize=len(payload),
                             address_format=32, memorysize_format=32)
        client.request_download(loc)
        chunk = 0xFFE  # ISO-TP cerceve sinirina gore ayarla
        seq = 1
        for i in range(0, len(payload), chunk):
            client.transfer_data(seq & 0xFF, payload[i : i + chunk])
            seq += 1
        client.request_transfer_exit()

    # --- yardimcilar ------------------------------------------------------
    def _enter_programming(self, client) -> None:
        from udsoncan.services import DiagnosticSessionControl

        client.change_session(
            DiagnosticSessionControl.Session.programmingSession
        )

    def _require_driver(self) -> None:
        if self.driver is None:
            raise IdentificationError("Once identify() cagir veya driver ver.")

    def _select_blocks(self, block_name: Optional[str]) -> List[MemoryBlock]:
        blocks = self.driver.memory_map()
        if block_name:
            return [self._block_by_name(block_name)]
        return blocks

    def _block_by_name(self, name: str) -> MemoryBlock:
        for blk in self.driver.memory_map():
            if blk.name == name:
                return blk
        raise KeyError(f"Blok yok: {name}")
