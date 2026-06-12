from __future__ import annotations

from autoflash.container import ToyXorContainerCodec


def test_toy_xor_container_codec_round_trip() -> None:
    codec = ToyXorContainerCodec()
    flat = b"virtual-calibration-block"

    encoded = codec.encode(flat)
    decoded = codec.decode(encoded)

    assert decoded == flat


def test_toy_xor_container_codec_changes_nonempty_input() -> None:
    codec = ToyXorContainerCodec()
    flat = b"\x00\x01\x02\x03\x04"

    assert codec.encode(flat) != flat


def test_toy_xor_container_codec_handles_empty_data() -> None:
    codec = ToyXorContainerCodec()

    assert codec.encode(b"") == b""
    assert codec.decode(b"") == b""
