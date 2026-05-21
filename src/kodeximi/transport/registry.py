from __future__ import annotations

from .base import Transport
from .fake import FakeTransport


def get_transport(name: str) -> Transport:
    if name == "fake":
        return FakeTransport()
    if name == "kimi-wire":
        raise NotImplementedError("kimi-wire transport is blocked until wire smoke succeeds.")
    raise ValueError(f"unknown transport: {name}")

