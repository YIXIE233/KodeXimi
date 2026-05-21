from __future__ import annotations

from .base import Transport
from .fake import FakeTransport
from .kimi_wire import KimiWireTransport


def get_transport(name: str) -> Transport:
    if name == "fake":
        return FakeTransport()
    if name == "kimi-wire":
        return KimiWireTransport()
    raise ValueError(f"unknown transport: {name}")
