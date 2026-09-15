import asyncio
from collections import deque
from logging import getLogger

log = getLogger(__name__)


def iter_entries(obj: dict | list):
    """Yields (key, value) pairs for dicts and (index, value) pairs for lists."""
    if isinstance(obj, dict):
        yield from obj.items()
    if isinstance(obj, list):
        yield from enumerate(obj)


async def spawn_tasks(obj) -> list[asyncio.Task]:
    """Wraps every coroutine found anywhere in the object in a task, in place."""
    pending = deque([obj])
    tasks = []

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in iter_entries(current):
                match value:
                    case list() | dict():
                        pending.append(value)
                    case _ if asyncio.iscoroutine(value):
                        current[key] = asyncio.create_task(value)
                        tasks.append(current[key])
    return tasks


async def resolve_tasks(obj) -> None:
    """Replaces every task found anywhere in the object by its result."""
    pending = deque([obj])

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in iter_entries(current):
                match value:
                    case asyncio.Task():
                        current[key] = value.result()
                    case list() | dict():
                        pending.append(value)


async def gather(obj, deep: bool = True) -> None:
    """Gathers coroutines in the object concurrently, replacing them with their results."""

    async def make_single_pass():
        tasks = await spawn_tasks(obj)
        if tasks:
            await asyncio.gather(*tasks)
            await resolve_tasks(obj)
            return True
        return False

    while await make_single_pass() and deep:
        pass
