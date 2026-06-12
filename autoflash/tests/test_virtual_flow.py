"""
Sanal ECU uzerinde regresyon testleri.

    pip install pytest
    pytest -q

Donanim gerektirmez. Flasher'in gercek kodunu sahte ECU'ya karsi calistirir.
"""

import logging
import os

import pytest
from udsoncan.exceptions import NegativeResponseException

from autoflash import Flasher
from autoflash.drivers import mock  # noqa: F401  (registry'ye kaydet)
from autoflash.registry import registry
from autoflash.virtual import VirtualCanConnection, VirtualECU

logging.getLogger("Connection").setLevel(logging.CRITICAL)
logging.getLogger("UdsClient").setLevel(logging.CRITICAL)

CAL_ADDR = 0x80000000


@pytest.fixture
def ecu():
    return VirtualECU()


@pytest.fixture
def flasher(ecu):
    return Flasher(VirtualCanConnection(ecu))


def test_driver_auto_match(flasher):
    info = flasher.identify()
    assert flasher.driver.name == "mock"
    assert info.vin == "WVWMOCK1234567890"


def test_registry_unknown_id_raises():
    from autoflash.exceptions import DriverNotFoundError

    with pytest.raises(DriverNotFoundError):
        registry.match("UNKNOWN_ECU_ID")


def test_read_round_trip(flasher, ecu, tmp_path):
    flasher.identify()
    paths = flasher.read(out_dir=str(tmp_path))
    assert len(paths) == 2
    cal = open(paths[0], "rb").read()
    # okunan .bin == ECU'daki blogun cozulmus hali
    assert cal == ecu.decoded_block(CAL_ADDR)
    assert len(cal) == 256


def test_write_success_updates_memory(flasher, ecu, tmp_path):
    flasher.identify()
    flasher.read(out_dir=str(tmp_path))
    cal = bytearray(open(tmp_path / "CAL.bin", "rb").read())
    cal[10] ^= 0xFF
    src = tmp_path / "CAL_tuned.bin"
    src.write_bytes(cal)

    flasher.write(files={"CAL": str(src)})
    assert ecu.decoded_block(CAL_ADDR)[10] == cal[10]


def test_security_access_required_for_write(ecu, tmp_path):
    # compute_key'i bozarsak seed-key tutmaz -> write reddedilmeli
    flasher = Flasher(VirtualCanConnection(ecu))
    flasher.identify()
    flasher.read(out_dir=str(tmp_path))
    flasher.driver.compute_key = lambda seed, level: b"\x00\x00\x00\x00"
    src = tmp_path / "CAL.bin"
    with pytest.raises(NegativeResponseException):
        flasher.write(files={"CAL": str(src)})


def test_bad_checksum_rejected(flasher, ecu, tmp_path):
    flasher.identify()
    flasher.read(out_dir=str(tmp_path))
    # checksum duzeltmeyi devre disi birak + dosyayi boz
    flasher.driver.correct_checksum = lambda data, block: data
    bad = bytearray(open(tmp_path / "CAL.bin", "rb").read())
    bad[-1] ^= 0xAA
    src = tmp_path / "CAL_bad.bin"
    src.write_bytes(bad)
    with pytest.raises(NegativeResponseException) as exc:
        flasher.write(files={"CAL": str(src)})
    assert exc.value.response.code == 0x72  # GeneralProgrammingFailure


def test_uds_service_sequence(flasher, ecu, tmp_path):
    """Dogru UDS servislerinin dogru sirada cagrildigini dogrula."""
    flasher.identify()
    flasher.read(out_dir=str(tmp_path))
    # read sirasinda upload(0x35) + transfer(0x36) + exit(0x37) cagrilmali
    assert 0x35 in ecu.log
    assert 0x36 in ecu.log
    assert 0x37 in ecu.log
