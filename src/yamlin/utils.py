from collections.abc import Awaitable
from time import time
from typing import Callable, TypeAlias, TypeVar

T = TypeVar("T")


Write: TypeAlias = Callable[[str], None]


async def measure(fn: Callable[[], Awaitable[T]]) -> tuple[float, T]:
    start = time()
    result = await fn()
    return (time() - start, result)


async def log_time(fn: Callable[[], Awaitable[T]], write: Write, label: str) -> T:
    elapsed, result = await measure(fn)
    write(f"{label}:\t{elapsed:.2f} seconds")
    return result
