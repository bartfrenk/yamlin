from asyncio import Task, create_task, gather, iscoroutine
from collections import deque
from logging import getLogger

log = getLogger(__name__)


def indexed(obj: dict | list):
    """Helper function to iterate over indexed collections."""
    if isinstance(obj, dict):
        yield from obj.items()
    if isinstance(obj, list):
        yield from enumerate(obj)


async def run_deferreds(obj) -> list[Task]:
    """Wraps coroutines found in the object in tasks and returns them."""
    pending = deque([obj])
    tasks = []

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in indexed(current):
                match value:
                    case list() | dict():
                        pending.append(value)
                    case _ if iscoroutine(value):
                        current[key] = create_task(value)
                        tasks.append(current[key])
    return tasks


async def replace_tasks(obj) -> None:
    """Replaces all tasks in the object by their results."""
    pending = deque([obj])

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in indexed(current):
                match value:
                    case Task():
                        current[key] = value.result()
                    case list() | dict():
                        pending.append(value)


async def force(obj, deep: bool = True) -> None:
    """Forces coroutines in the object concurrently."""

    async def make_single_pass():
        tasks = await run_deferreds(obj)
        if tasks:
            await gather(*tasks)
            await replace_tasks(obj)
            return True
        return False

    while await make_single_pass() and deep:
        pass
