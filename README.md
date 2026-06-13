# AutoFlash

![Tests](https://github.com/EmreUludasdemir/Ecu-Unlock-Tool/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Scope](https://img.shields.io/badge/scope-educational%20virtual%20ECU-orange)

AutoFlash is an educational ECU flashing framework skeleton. It models the
architecture of professional read/write tools with a virtual UDS ECU simulator,
a mock ECU driver, driver safety metadata, operation planning, dry-run support,
audit logging, a CLI, and pytest regression tests.

It does not implement real ECU unlock exploits, OEM seed-key algorithms,
RSA/SBOOT/CBOOT bypasses, boot password recovery, emissions defeat, or real ECU
write support.

## Architecture

```text
                 +------------------+
   CLI / app  -> |     Flasher      |  orchestration: identify -> read/write
                 +--------+---------+
                          |
        +-----------------+------------------+
        |                                    |
+-------v--------+                  +--------v---------+
|  BaseConnection|                  |    ECUDriver     |
|  (transport)   |                  |  (plugin)        |
+-------+--------+                  +--------+---------+
        |                                    |
  OBD / Bench / Boot              seed-key provider,
  (CAN/ISO-TP, BSL...)            memory map, container, checksum
```

| Layer | File | Responsibility |
| --- | --- | --- |
| Transport | `autoflash/connection.py` | OBD, CAN/ISO-TP, bench, and boot transport abstraction |
| UDS flow | `autoflash/flasher.py` | Identify, read, write orchestration |
| Driver API | `autoflash/ecu_driver.py` | ECU-family contract |
| Registry | `autoflash/registry.py` | ECU-to-driver matching |
| Virtual ECU | `autoflash/virtual.py` | Hardware-free UDS simulator |
| Mock driver | `autoflash/drivers/mock.py` | Safe reference driver for tests |
| CLI | `autoflash/cli.py` | `identify`, `capabilities`, `read`, and `write` commands |

## Quick Start

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python demo_virtual.py
python -m pytest -q
```

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements-dev.txt
py demo_virtual.py
py -m pytest -q
```

If the Windows `python` command opens the Microsoft Store alias, use the `py`
launcher or disable the `python.exe` / `python3.exe` App Execution Aliases in
Windows settings.

## CLI

Virtual ECU mode does not require hardware:

```bash
python -m autoflash.cli identify --virtual
python -m autoflash.cli capabilities --virtual
python -m autoflash.cli read --virtual --out ./dump
python -m autoflash.cli write --virtual --block CAL --file ./dump/CAL.bin --plan
python -m autoflash.cli write --virtual --block CAL --file ./dump/CAL.bin --dry-run
python -m autoflash.cli write --virtual --block CAL --file ./dump/CAL.bin --dry-run --audit-log ./logs/audit.jsonl
python -m autoflash.cli write --virtual --block CAL --file ./dump/CAL.bin
```

The virtual ECU answers raw UDS bytes through the same flasher path used by the
transport abstraction. The only transport swap is:

```text
VirtualCanConnection -> IsoTpCanConnection
```

SocketCAN examples are kept as framework placeholders for owned/authorized
research hardware. Real ECU write, unlock, and bypass support is intentionally
not implemented.

```bash
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
python -m autoflash.cli identify --channel can0
python -m autoflash.cli read --channel can0 --out ./dump
```

## Current Milestone

- Virtual ECU simulator is implemented.
- Mock ECU driver is implemented.
- CLI `--virtual` mode is implemented.
- Driver capabilities and fail-closed safety metadata are implemented.
- Operation plan, dry-run, and JSONL audit logging are implemented.
- Regression tests are available and run in GitHub Actions.
- Real ECU support is not implemented.
- Simos18 integration is planned as a read-only research milestone.
- Real hardware write/recovery work is intentionally left for the end.

## Documentation

See [docs/README.md](docs/README.md) for the project documentation index.

Key planning documents:

- [Driver capabilities and safety policy](docs/driver_capabilities_policy.md)
- [Operation plan and dry-run](docs/operation_plan_and_dry_run.md)
- [SeedKeyProvider research plan](docs/seed_key_provider_plan.md)
- [Memory map database plan](docs/memory_map_database_plan.md)
- [Safe research roadmap](docs/safe_research_roadmap.md)
- [Bench hardware notes](docs/bench_hardware_notes.md)

The Simos18 read-only plan is maintained on the `simos18-readonly` branch.

## Adding an ECU Driver

Add a module under `autoflash/drivers/`, subclass `ECUDriver`, register it with
the registry, and implement the family-specific methods for identification,
memory maps, safe key handling, container decoding/encoding, and checksum
correction.

Drivers must declare capabilities. Research stubs should fail closed and must
not advertise real write/unlock support.

## Roadmap

1. [x] Framework skeleton
2. [x] Virtual ECU simulator, mock driver, and tests
3. [x] Read pipeline in simulation
4. [x] Driver capability and safety policy layer
5. [x] Operation plan, dry-run, and audit logging
6. [ ] Simos18 read-only analysis branch
7. [ ] Owned/authorized hardware read validation
8. [ ] Bench mode planning
9. [ ] Boot/BSL recovery planning
10. [ ] Real write/recovery only after explicit safety gates

## Safety Scope

AutoFlash is for education, protocol learning, virtual simulation, and
owned/authorized ECU research.

Out of scope:

- No real ECU unlock support.
- No OEM seed-key algorithms.
- No RSA/SBOOT/CBOOT bypasses.
- No boot password recovery.
- No emissions defeat, DPF, EGR, SCR, or AdBlue removal.
- No unauthorized ECU access.
- No real ECU write support.
- Virtual write is limited to the mock ECU simulator.

## References

- `bri3d/VW_Flash`, `bri3d/Simos18_SBOOT`, `bri3d/TC1791_CAN_BSL`
- `pylessard/python-udsoncan`
- `python-can`
- `can-isotp`
