"""
Sanal ECU simulatoru (Asama 1).

Amac: donanim olmadan tum akisi test etmek. Gercek udsoncan.Client'a, ham UDS
byte seviyesinde cevap veren stateful bir sahte ECU baglar. Boylece Flasher'in
GERCEK kodu (session, security access, upload/download) test edilir; sadece
fiziksel transport sahte olur.

Iceri girisler:
    VirtualECU            - ISO 14229 isteklerini parse edip cevap ureten ECU
    VirtualUdsConnection  - udsoncan BaseConnection; istegi ECU'ya pipeler
    VirtualCanConnection  - framework'un BaseConnection'i; Flasher buna baglanir

Kullanilan "toy" algoritmalar (xor_crypt / apply_checksum / seed_to_key) gercek
bir uretici algoritmasi DEGILDIR; sadece akisin uctan uca kapanmasi icin
ECU ile mock driver'in uzerinde anlastigi basit, tersinir fonksiyonlardir.
"""

from __future__ import annotations

import os
import queue
from typing import Dict, Optional

from udsoncan.connections import BaseConnection as _UdsBaseConnection
from udsoncan.exceptions import TimeoutException

from .checksum import ToyCrc32Checksum
from .connection import BaseConnection as _FrameworkConnection
from .container import DEFAULT_TOY_XOR_KEY, ToyXorContainerCodec
from .security import MOCK_XOR_ROTATE_SECRET, MockXorRotateSeedKeyProvider

# --- toy kripto/checksum (ECU <-> mock driver ortak sozlesmesi) -------------

_XOR_KEY = DEFAULT_TOY_XOR_KEY
_KEY_SECRET = MOCK_XOR_ROTATE_SECRET
_CHECKSUM = ToyCrc32Checksum()
_CODEC = ToyXorContainerCodec(_XOR_KEY)
_SEED_KEY_PROVIDER = MockXorRotateSeedKeyProvider(_KEY_SECRET)


def xor_crypt(data: bytes, key: bytes = _XOR_KEY) -> bytes:
    """Simetrik XOR 'sifreleme' (oyuncak)."""
    if key == _XOR_KEY:
        return _CODEC.encode(data)
    return ToyXorContainerCodec(key).encode(data)


def apply_checksum(flat: bytes) -> bytes:
    """Son 4 byte = crc32(geri kalan). Checksum 'duzeltme'."""
    return _CHECKSUM.apply(flat)


def verify_checksum(flat: bytes) -> bool:
    return _CHECKSUM.verify(flat)


def seed_to_key(seed: bytes, secret: int = _KEY_SECRET) -> bytes:
    """Seed -> key (oyuncak): XOR + rotate. Gercek SA2 degildir."""
    if secret == _KEY_SECRET:
        return _SEED_KEY_PROVIDER.compute_key(seed, level=1)
    return MockXorRotateSeedKeyProvider(secret).compute_key(seed, level=1)


# --- NRC kisaltmalari -------------------------------------------------------
NRC_SERVICE_NOT_SUPPORTED = 0x11
NRC_CONDITIONS_NOT_CORRECT = 0x22
NRC_REQUEST_OUT_OF_RANGE = 0x31
NRC_SECURITY_DENIED = 0x33
NRC_INVALID_KEY = 0x35
NRC_GENERAL_PROGRAMMING_FAILURE = 0x72


class VirtualECU:
    """ISO 14229 (UDS) konusan, bellek tutan stateful sahte ECU."""

    def __init__(
        self,
        vin: str = "WVWMOCK1234567890",
        sw: str = "MOCK0001",
        blocks: Optional[Dict[int, int]] = None,
        require_security_for_read: bool = False,
        upload_chunk: int = 64,
    ) -> None:
        self.vin = vin
        self.sw = sw
        self.require_security_for_read = require_security_for_read
        self.upload_chunk = upload_chunk

        self.session = 0x01
        self.unlocked = False
        self._seed = b"\x00\x00\x00\x00"

        # memory[address] = blogun ENCODED (sifreli) hali
        self.memory: Dict[int, bytes] = {}
        blocks = blocks or {0x80000000: 256, 0x80100000: 256}
        for addr, size in blocks.items():
            payload = os.urandom(size - 4) + b"\x00\x00\x00\x00"
            flat = apply_checksum(payload)          # gecerli checksum'li blok
            self.memory[addr] = xor_crypt(flat)     # encrypted olarak sakla

        self._dl: Optional[dict] = None             # aktif download
        self._ul: Optional[dict] = None             # aktif upload
        self.log = []                               # gelen SID'lerin izi (test/debug)

    # test yardimcisi: bir blogun cozulmus (flat) halini ver
    def decoded_block(self, address: int) -> bytes:
        return xor_crypt(self.memory[address])

    # --- ana giris --------------------------------------------------------
    def process_request(self, req: bytes) -> bytes:
        if not req:
            return self._neg(0x00, NRC_SERVICE_NOT_SUPPORTED)
        sid = req[0]
        self.log.append(sid)
        handler = {
            0x10: self._session,
            0x27: self._security,
            0x22: self._read_did,
            0x34: self._request_download,
            0x35: self._request_upload,
            0x36: self._transfer,
            0x37: self._transfer_exit,
            0x31: self._routine,
        }.get(sid)
        if handler is None:
            return self._neg(sid, NRC_SERVICE_NOT_SUPPORTED)
        return handler(req)

    # --- servisler --------------------------------------------------------
    def _session(self, req: bytes) -> bytes:
        sub = req[1]
        self.session = sub
        # 0x50 sub + P2/P2* timing (default 50ms / 5000ms)
        return bytes([0x50, sub, 0x00, 0x32, 0x01, 0xF4])

    def _security(self, req: bytes) -> bytes:
        sub = req[1]
        if sub % 2 == 1:  # requestSeed
            self._seed = b"\x00\x00\x00\x00" if self.unlocked else os.urandom(4)
            return bytes([0x67, sub]) + self._seed
        # sendKey
        key = req[2:]
        if key == seed_to_key(self._seed):
            self.unlocked = True
            return bytes([0x67, sub])
        return self._neg(0x27, NRC_INVALID_KEY)

    def _read_did(self, req: bytes) -> bytes:
        did = (req[1] << 8) | req[2]
        if did == 0xF190:
            data = self.vin.encode("ascii")
        elif did == 0xF188:
            data = self.sw.encode("ascii")
        else:
            return self._neg(0x22, NRC_REQUEST_OUT_OF_RANGE)
        return bytes([0x62, req[1], req[2]]) + data

    def _parse_addr_size(self, req: bytes):
        alfid = req[2]
        addr_len = alfid & 0x0F
        size_len = (alfid >> 4) & 0x0F
        i = 3
        addr = int.from_bytes(req[i : i + addr_len], "big"); i += addr_len
        size = int.from_bytes(req[i : i + size_len], "big")
        return addr, size

    def _request_download(self, req: bytes) -> bytes:
        if self.session != 0x02:
            return self._neg(0x34, NRC_CONDITIONS_NOT_CORRECT)
        if not self.unlocked:
            return self._neg(0x34, NRC_SECURITY_DENIED)
        addr, size = self._parse_addr_size(req)
        self._dl = {"addr": addr, "size": size, "buf": bytearray()}
        return bytes([0x74, 0x20, 0x0F, 0xFF])  # maxNumberOfBlockLength = 0x0FFF

    def _request_upload(self, req: bytes) -> bytes:
        if self.require_security_for_read and not self.unlocked:
            return self._neg(0x35, NRC_SECURITY_DENIED)
        addr, size = self._parse_addr_size(req)
        block = self.memory.get(addr)
        if block is None:
            return self._neg(0x35, NRC_REQUEST_OUT_OF_RANGE)
        self._ul = {"data": block[:size], "pos": 0}
        return bytes([0x75, 0x20, 0x0F, 0xFF])

    def _transfer(self, req: bytes) -> bytes:
        seq = req[1]
        if self._dl is not None:                 # download: veri al
            self._dl["buf"].extend(req[2:])
            return bytes([0x76, seq])
        if self._ul is not None:                 # upload: veri don
            ul = self._ul
            chunk = ul["data"][ul["pos"] : ul["pos"] + self.upload_chunk]
            ul["pos"] += len(chunk)
            return bytes([0x76, seq]) + chunk
        return self._neg(0x36, NRC_CONDITIONS_NOT_CORRECT)

    def _transfer_exit(self, req: bytes) -> bytes:
        if self._dl is not None:
            buf = bytes(self._dl["buf"])
            addr = self._dl["addr"]
            self._dl = None
            plain = xor_crypt(buf)
            if not verify_checksum(plain):       # CHECKSUM GATE
                return self._neg(0x37, NRC_GENERAL_PROGRAMMING_FAILURE)
            self.memory[addr] = buf              # yeni blogu yaz
            return bytes([0x77])
        if self._ul is not None:
            self._ul = None
            return bytes([0x77])
        return self._neg(0x37, NRC_CONDITIONS_NOT_CORRECT)

    def _routine(self, req: bytes) -> bytes:
        # RoutineControl (orn. eraseMemory) - her zaman OK
        return bytes([0x71]) + req[1:4]

    @staticmethod
    def _neg(sid: int, nrc: int) -> bytes:
        return bytes([0x7F, sid, nrc])


# --- udsoncan transport: client <-> VirtualECU ------------------------------
class VirtualUdsConnection(_UdsBaseConnection):
    """udsoncan.Client'in kullanacagi senkron sanal baglanti."""

    def __init__(self, ecu: VirtualECU, name: str = "virtual") -> None:
        super().__init__(name)
        self.ecu = ecu
        self.opened = False
        self._rx: "queue.Queue[bytes]" = queue.Queue()

    def open(self):
        self.opened = True
        return self

    def close(self):
        self.opened = False

    def is_open(self) -> bool:
        return self.opened

    def empty_rxqueue(self):
        while not self._rx.empty():
            self._rx.get_nowait()

    def specific_send(self, payload: bytes, timeout: Optional[float] = None):
        resp = self.ecu.process_request(bytes(payload))
        if resp is not None:
            self._rx.put(resp)

    def specific_wait_frame(self, timeout: Optional[float] = None) -> Optional[bytes]:
        try:
            return self._rx.get(block=True, timeout=timeout or 1.0)
        except queue.Empty:
            raise TimeoutException("VirtualECU cevap vermedi")


# --- framework connection: Flasher buna baglanir ----------------------------
class VirtualCanConnection(_FrameworkConnection):
    """Flasher icin sanal transport. Gercek IsoTpCanConnection'in yerini alir."""

    mode = "virtual"

    def __init__(self, ecu: Optional[VirtualECU] = None) -> None:
        self.ecu = ecu or VirtualECU()
        self._uds = VirtualUdsConnection(self.ecu)

    def open(self) -> None:
        self._uds.open()

    def close(self) -> None:
        self._uds.close()

    def uds_connection(self):
        return self._uds
