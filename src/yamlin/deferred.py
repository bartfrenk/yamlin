from abc import ABC, abstractmethod
from asyncio import Task, create_task, gather
from collections import deque


class Deferred(ABC):
    @abstractmethod
    async def result(self): ...


def indexed(obj: dict | list):
    """Helper function to iterate over indexed collections."""
    if isinstance(obj, dict):
        yield from obj.items()
    if isinstance(obj, list):
        yield from enumerate(obj)


async def run_deferreds(obj) -> list[Task]:
    """Runs all deferred tasks in the object and returns a list of tasks."""
    pending = deque([obj])
    tasks = []

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in indexed(current):
                if isinstance(value, (list, dict)):
                    pending.append(value)
                if isinstance(value, Deferred):
                    current[key] = create_task(value.result())
                    tasks.append(current[key])
    return tasks


async def replace_tasks(obj) -> None:
    """Replaces all tasks in the object by their results."""
    pending = deque([obj])

    while pending:
        current = pending.popleft()
        if isinstance(current, (list, dict)):
            for key, value in indexed(current):
                if isinstance(value, (list, dict)):
                    pending.append(value)
                if isinstance(value, Task):
                    current[key] = value.result()


async def force(obj, deep: bool = True) -> None:
    """Forces deferreds in the object concurrently."""

    async def make_single_pass():
        tasks = await run_deferreds(obj)
        if tasks:
            await gather(*tasks)
            await replace_tasks(obj)
            return True
        return False

    while await make_single_pass() and deep:
        pass
