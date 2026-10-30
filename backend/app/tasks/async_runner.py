"""Shared async runner for sync Celery workers.

All Celery task modules must use this single loop to avoid async DB pool
connections being bound to different event loops.
"""

import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")

_WORKER_LOOP: asyncio.AbstractEventLoop | None = None


def run_async(coro: Awaitable[T]) -> T:
    global _WORKER_LOOP
    if _WORKER_LOOP is None or _WORKER_LOOP.is_closed():
        _WORKER_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_WORKER_LOOP)
    return _WORKER_LOOP.run_until_complete(coro)
