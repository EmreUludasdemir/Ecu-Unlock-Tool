from __future__ import annotations

import pytest

from autoflash.data.memory_maps import build_default_memory_map_database
from autoflash.drivers.mock import MockDriver
from autoflash.drivers.simos18 import Simos18Driver
from autoflash.memory_map import (
    EcuFamilySpec,
    MemoryBlockSpec,
    MemoryMapDatabase,
    MemoryMapError,
)


def test_memory_block_spec_can_be_created() -> None:
    block = MemoryBlockSpec("CAL", address=0x1000, size=256)

    assert block.name == "CAL"
    assert block.read_only is True
    assert block.compression == "none"
    assert block.encryption == "none"


def test_ecu_family_spec_can_be_created() -> None:
    block = MemoryBlockSpec("CAL", address=0x1000, size=256)
    family = EcuFamilySpec(
        family="demo",
        display_name="Demo ECU",
        supported_ids=("DEMO",),
        blocks=(block,),
    )

    assert family.family == "demo"
    assert family.blocks == (block,)


def test_memory_map_database_register_and_get() -> None:
    db = MemoryMapDatabase()
    family = EcuFamilySpec(
        family="demo",
        display_name="Demo ECU",
        supported_ids=("DEMO",),
        blocks=(MemoryBlockSpec("CAL", address=0x1000, size=256),),
    )

    db.register(family)

    assert db.get("demo") is family
    assert db.list_families() == ["demo"]


def test_memory_map_database_rejects_duplicate_family() -> None:
    db = MemoryMapDatabase()
    family = EcuFamilySpec(
        family="demo",
        display_name="Demo ECU",
        supported_ids=("DEMO",),
        blocks=(MemoryBlockSpec("CAL", address=0x1000, size=256),),
    )

    db.register(family)

    with pytest.raises(MemoryMapError, match="already registered"):
        db.register(family)


def test_memory_map_database_rejects_unknown_family() -> None:
    db = MemoryMapDatabase()

    with pytest.raises(MemoryMapError, match="Unknown ECU family"):
        db.get("missing")


def test_memory_map_database_matches_by_sw_prefix() -> None:
    db = build_default_memory_map_database()

    match = db.match_by_sw_id("MOCK0001")

    assert match is not None
    assert match.family == "mock"


def test_default_memory_map_database_contains_mock_and_simos18() -> None:
    db = build_default_memory_map_database()

    assert db.list_families() == ["mock", "simos18"]
    assert db.get("mock").display_name == "Virtual Mock ECU"
    assert "read-only research" in db.get("simos18").notes


def test_mock_driver_memory_map_uses_metadata_placeholders() -> None:
    names = [block.name for block in MockDriver().memory_map()]

    assert names == ["CAL", "ASW"]


def test_simos18_driver_memory_map_uses_readonly_placeholders() -> None:
    blocks = Simos18Driver().memory_map()
    names = [block.name for block in blocks]

    assert names == ["CAL", "ASW1"]
    assert all(block.compression == "lzss" for block in blocks)
    assert all(block.encryption == "aes-cbc" for block in blocks)


def test_simos18_dangerous_methods_remain_disabled() -> None:
    driver = Simos18Driver()
    block = driver.memory_map()[0]

    with pytest.raises(NotImplementedError):
        driver.compute_key(b"\x01\x02\x03\x04", level=1)
    with pytest.raises(NotImplementedError):
        driver.decode_container(b"raw", block)
    with pytest.raises(NotImplementedError):
        driver.encode_container(b"flat", block)
    with pytest.raises(NotImplementedError):
        driver.correct_checksum(b"flat", block)
