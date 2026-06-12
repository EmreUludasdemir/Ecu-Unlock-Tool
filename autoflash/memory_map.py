"""Structured ECU family and memory block metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


class MemoryMapError(ValueError):
    """Raised when memory map metadata is missing or invalid."""


@dataclass(frozen=True)
class MemoryBlockSpec:
    name: str
    address: int
    size: int
    description: str = ""
    read_only: bool = True
    compression: str = "none"
    encryption: str = "none"


@dataclass(frozen=True)
class EcuFamilySpec:
    family: str
    display_name: str
    supported_ids: tuple[str, ...]
    blocks: tuple[MemoryBlockSpec, ...]
    notes: str = ""


class MemoryMapDatabase:
    """In-memory registry of ECU family memory map metadata."""

    def __init__(self) -> None:
        self._families: Dict[str, EcuFamilySpec] = {}

    def register(self, spec: EcuFamilySpec) -> None:
        if not spec.family:
            raise MemoryMapError("ECU family name must not be empty.")
        if spec.family in self._families:
            raise MemoryMapError(f"ECU family already registered: {spec.family}")
        self._families[spec.family] = spec

    def get(self, family: str) -> EcuFamilySpec:
        try:
            return self._families[family]
        except KeyError as exc:
            raise MemoryMapError(f"Unknown ECU family: {family}") from exc

    def match_by_sw_id(self, sw_id: str) -> Optional[EcuFamilySpec]:
        for spec in self._families.values():
            if any(sw_id.startswith(prefix) for prefix in spec.supported_ids):
                return spec
        return None

    def list_families(self) -> list[str]:
        return sorted(self._families)
