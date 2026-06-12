"""
Sanal ECU uzerinde uctan uca demo.

    python demo_virtual.py

Donanim YOK. Tum akis (identify -> read -> write -> checksum gate) sahte ECU
uzerinde calisir. Flasher'in gercek kodu test edilir; sadece transport sahte.
"""

import os
import tempfile
import logging

import udsoncan
from udsoncan.exceptions import NegativeResponseException

from autoflash import Flasher
from autoflash.drivers import *  # noqa: F401,F403  (driver'lari kaydet)
from autoflash.virtual import VirtualCanConnection, VirtualECU, xor_crypt

logging.getLogger("Connection").setLevel(logging.CRITICAL)
logging.getLogger("UdsClient").setLevel(logging.CRITICAL)


def banner(t):
    print("\n" + "=" * 56 + f"\n {t}\n" + "=" * 56)


def main():
    ecu = VirtualECU()
    conn = VirtualCanConnection(ecu)
    flasher = Flasher(conn)

    banner("1) IDENTIFY  (driver auto-match)")
    info = flasher.identify()
    print(f"  ECU    : {info.name}")
    print(f"  VIN    : {info.vin}")
    print(f"  driver : {flasher.driver.name}")
    assert flasher.driver.name == "mock", "auto-match basarisiz"

    banner("2) READ  (upload -> decode_container -> .bin)")
    out = tempfile.mkdtemp()
    paths = flasher.read(out_dir=out)
    for p in paths:
        size = os.path.getsize(p)
        print(f"  okundu : {os.path.basename(p)}  ({size} byte)")
    # dogrula: okunan .bin, ECU'daki blogun cozulmus hali mi?
    cal = open(paths[0], "rb").read()
    assert cal == ecu.decoded_block(0x80000000), "read round-trip hatali"
    print("  OK     : read round-trip dogru (decode == ECU memory)")

    banner("3) WRITE  (security access -> checksum-correct -> flash)")
    # CAL'i biraz degistir, dosyaya yaz, sonra flash'la
    modified = bytearray(cal)
    modified[10] ^= 0xFF  # tek byte degistir
    src = os.path.join(out, "CAL_tuned.bin")
    open(src, "wb").write(modified)
    flasher.write(files={"CAL": src})
    print("  OK     : flash kabul edildi (seed-key + checksum gecti)")
    # ECU'da gercekten degisti mi?
    assert ecu.decoded_block(0x80000000)[10] == modified[10]
    print("  OK     : ECU memory guncellendi, checksum yeniden gecerli")

    banner("4) CHECKSUM GATE  (bozuk checksum reddedilmeli)")
    # correct_checksum'i devre disi birak -> bozuk dosya -> ECU reddetmeli
    ecu.unlocked = False  # yeniden kilitle (gercekci)
    flasher.driver.correct_checksum = lambda data, block: data  # no-op
    bad = bytearray(modified)
    bad[-1] ^= 0xAA  # checksum'u boz
    badsrc = os.path.join(out, "CAL_bad.bin")
    open(badsrc, "wb").write(bad)
    try:
        flasher.write(files={"CAL": badsrc})
        print("  HATA   : bozuk checksum kabul edildi (olmamaliydi)")
    except NegativeResponseException as e:
        print(f"  OK     : ECU bozuk checksum'u reddetti -> {e.response.code_name}")

    banner("SONUC")
    print("  Tum akis sanal ECU uzerinde calisti. Donanim gelince tek")
    print("  degisiklik: VirtualCanConnection -> IsoTpCanConnection.")


if __name__ == "__main__":
    main()
