# pyright: reportUnknownArgumentType=false, reportAny=false, reportExplicitAny=false

import asyncio
from collections import deque
from collections.abc import Iterator
from logging import getLogger
from typing import Any

log = getLogger(__name__)

Container = dict[Any, Any] | list[Any]


def iter_entries(obj: Container) -> Iterator[tuple[Any, Any]]:
    """Yields (key, value) pairs for dicts and (index, value) pairs for lists."""
    if isinstance(obj, dict):
        yield from obj.items()
    if isinstance(obj, list):
        yield from enumerate(obj)


async def spawn_tasks(obj: Container) -> list[asyncio.Task[Any]]:
    """Wraps every coroutine found anywhere in the object in a task, in place."""
    pending: deque[Container] = deque([obj])
    tasks: list[asyncio.Task[Any]] = []

    while pending:
        current = pending.popleft()
        for key, value in iter_entries(current):
            match value:
                case list() | dict():
                    pending.append(value)
                case _ if asyncio.iscoroutine(value):
                    current[key] = asyncio.create_task(value)
                    tasks.append(current[key])
                case _:
                    pass
    return tasks


async def resolve_tasks(obj: Container) -> None:
    """Replaces every task found anywhere in the object by its result."""
    pending: deque[Container] = deque([obj])

    while pending:
        current = pending.popleft()
        for key, value in iter_entries(current):
            match value:
                case asyncio.Task():
                    current[key] = value.result()
                case list() | dict():
                    pending.append(value)
                case _:
                    pass


async def gather(obj: Container, deep: bool = True) -> None:
    """Gathers coroutines in the object concurrently, replacing them with their results."""

    async def make_single_pass() -> bool:
        tasks = await spawn_tasks(obj)
        if tasks:
            await asyncio.gather(*tasks)  # pyright: ignore[reportUnusedCallResult]
            await resolve_tasks(obj)
            return True
        return False

    while await make_single_pass() and deep:
        pass
