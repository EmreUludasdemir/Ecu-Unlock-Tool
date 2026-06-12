"""
Transport katmani.

Autotuner'in 3 modu (OBD / Bench / Boot) burada tek bir `BaseConnection`
arayuzu altinda soyutlanir. Flasher, hangi mod oldugunu bilmeden calisir;
sadece bir UDS connection nesnesi ister.

  OBD   -> aractaki diagnostik soketten CAN/ISO-TP
  Bench -> ECU sokulmus, dogrudan pinout uzerinden CAN/SPI
  Boot  -> Tricore BSL / JTAG gibi bootloader erisimi (kilitli/olu ECU kurtarma)

Burada calisan tam ornek OBD (SocketCAN + ISO-TP). Bench/Boot iskelet olarak
birakildi; her biri ayri bir donanim entegrasyonu isidir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .exceptions import ConnectionFailed


class BaseConnection(ABC):
    """Bir ECU'ya giden tek bir fiziksel link."""

    mode: str = "base"

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def uds_connection(self):
        """udsoncan.Client'in kullanabilecegi bir connection nesnesi dondur."""
        ...

    def __enter__(self) -> "BaseConnection":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class IsoTpCanConnection(BaseConnection):
    """
    OBD modu: Linux SocketCAN + ISO-TP (ISO 15765-2) uzerinden UDS.

    Standart OBD adresleri:
        txid = 0x7E0  (tester -> ECU)
        rxid = 0x7E8  (ECU -> tester)
    ECU'ya gore degisir; bench/boot'ta farkli ID'ler kullanilir.
    """

    mode = "obd"

    def __init__(
        self,
        channel: str = "can0",
        txid: int = 0x7E0,
        rxid: int = 0x7E8,
        extended: bool = False,
    ) -> None:
        self.channel = channel
        self.txid = txid
        self.rxid = rxid
        self.extended = extended
        self._conn = None

    def _build(self):
        # Importlari lazy tutuyoruz ki paket donanim/bagimliliklar olmadan da
        # incelenebilsin.
        try:
            import isotp
            from udsoncan.connections import IsoTPSocketConnection
        except ImportError as e:  # pragma: no cover
            raise ConnectionFailed(
                "udsoncan + can-isotp gerekli: pip install udsoncan can-isotp python-can"
            ) from e

        mode = (
            isotp.AddressingMode.Normal_29bits
            if self.extended
            else isotp.AddressingMode.Normal_11bits
        )
        addr = isotp.Address(mode, rxid=self.rxid, txid=self.txid)
        return IsoTPSocketConnection(self.channel, addr)

    def open(self) -> None:
        self._conn = self._build()
        self._conn.open()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def uds_connection(self):
        if self._conn is None:
            raise ConnectionFailed("Connection acik degil - once open() cagir.")
        return self._conn


class BenchConnection(BaseConnection):
    """
    Bench modu iskeleti.

    ECU masada, dogrudan pinout uzerinden (genelde yine CAN ama bazen SPI/UART
    flash arayuzu). Pratikte ya yine ISO-TP ya da uretici-spesifik bir bootmode
    protokolu olur. Buraya kendi bench donanimini (orn. baska bir CAN kanali +
    guc/clock kontrolu) baglarsin.
    """

    mode = "bench"

    def open(self) -> None:
        raise NotImplementedError("Bench modu donanima ozel - kendin implemente et.")

    def close(self) -> None:
        pass

    def uds_connection(self):
        raise NotImplementedError


class BootConnection(BaseConnection):
    """
    Boot modu iskeleti (Infineon Tricore BSL vb.).

    Kilitli veya brick olmus ECU'lari kurtarmak icin kullanilir. CPU'yu BSL'e
    sokmak icin donanim pinleri + ozel bir indirme protokolu gerekir; bu UDS
    degildir, ayri bir transport'tur. Referans: bri3d/TC1791_CAN_BSL.
    """

    mode = "boot"

    def open(self) -> None:
        raise NotImplementedError("Boot/BSL modu donanima ozel - kendin implemente et.")

    def close(self) -> None:
        pass

    def uds_connection(self):
        raise NotImplementedError
