"""
AutoFlash CLI.

Ornekler:
    python -m autoflash.cli identify --channel can0
    python -m autoflash.cli read --channel can0 --out ./dump
    python -m autoflash.cli write --channel can0 --block CAL --file ./tune/CAL.bin
"""

from __future__ import annotations

import argparse
import sys

from .connection import BaseConnection, IsoTpCanConnection
from .drivers import mock  # noqa: F401  (mock driver'i registry'ye yukle)
from .drivers import simos18  # noqa: F401  (gercek platform driver'ini registry'ye yukle)
from .flasher import Flasher
from .virtual import VirtualCanConnection, VirtualECU


def _connection(args) -> BaseConnection:
    if args.virtual:
        return VirtualCanConnection(VirtualECU())
    return IsoTpCanConnection(
        channel=args.channel,
        txid=int(args.txid, 0),
        rxid=int(args.rxid, 0),
    )


def cmd_identify(args) -> int:
    with _connection(args) as conn:
        flasher = Flasher(conn)
        info = flasher.identify()
    print(f"ECU   : {info.name}")
    print(f"VIN   : {info.vin}")
    print(f"SW    : {info.sw_number}")
    print(f"Driver: {flasher.driver.name}")
    return 0


def cmd_read(args) -> int:
    with _connection(args) as conn:
        flasher = Flasher(conn)
        flasher.identify()
        paths = flasher.read(out_dir=args.out, block_name=args.block)
    for p in paths:
        print("yazildi:", p)
    return 0


def cmd_write(args) -> int:
    with _connection(args) as conn:
        flasher = Flasher(conn)
        flasher.identify()
        caps = flasher.driver.capabilities()
        if not args.virtual and not caps.allows_write():
            print(
                "write reddedildi: driver real ECU write support beyan etmiyor.",
                file=sys.stderr,
            )
            return 2
        flasher.write(files={args.block: args.file})
    print("flash tamam:", args.block)
    return 0


def cmd_capabilities(args) -> int:
    with _connection(args) as conn:
        flasher = Flasher(conn)
        flasher.identify()
        caps = flasher.driver.capabilities()
    _print_capabilities(caps)
    return 0


def _print_capabilities(caps) -> None:
    modes = ", ".join(mode.value for mode in caps.supported_connection_modes)
    print(f"driver: {caps.driver_name}")
    print(f"safety_level: {caps.safety_level.value}")
    print(f"connection_modes: {modes}")
    print(f"identify_supported: {str(caps.identify_supported).lower()}")
    print(f"read_supported: {str(caps.read_supported).lower()}")
    print(f"write_supported: {str(caps.write_supported).lower()}")
    print(
        "security_access_supported: "
        f"{str(caps.security_access_supported).lower()}"
    )
    print(f"real_ecu_supported: {str(caps.real_ecu_supported).lower()}")
    print(f"allows_write: {str(caps.allows_write()).lower()}")
    print(f"notes: {caps.notes}")


def _add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--virtual", action="store_true", help="Sanal ECU kullan")
    parser.add_argument("--channel", default="can0", help="SocketCAN kanali")
    parser.add_argument("--txid", default="0x7E0")
    parser.add_argument("--rxid", default="0x7E8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autoflash")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("identify", help="ECU'yu tani")
    _add_connection_args(sp)
    sp.set_defaults(func=cmd_identify)

    sp = sub.add_parser("read", help="Firmware oku")
    _add_connection_args(sp)
    sp.add_argument("--out", default="./dump")
    sp.add_argument("--block", default=None)
    sp.set_defaults(func=cmd_read)

    sp = sub.add_parser("capabilities", help="Driver capability bilgisini yaz")
    _add_connection_args(sp)
    sp.set_defaults(func=cmd_capabilities)

    sp = sub.add_parser("write", help="Firmware yaz")
    _add_connection_args(sp)
    sp.add_argument("--block", required=True)
    sp.add_argument("--file", required=True)
    sp.set_defaults(func=cmd_write)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
