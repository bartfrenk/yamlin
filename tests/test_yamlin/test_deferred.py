from asyncio import sleep
from time import time
from typing import Any, Tuple

import pytest

from yamlin.deferred import Deferred, force


class Box(Deferred):
    def __init__(self, value):
        self.value = value

    async def result(self):
        return self.value


class Wait(Deferred):
    def __init__(self, value, *, delay=1):
        self.value = value
        self.delay = delay

    async def result(self):
        await sleep(self.delay)
        return self.value


async def measure(fn) -> float:
    start = time()
    await fn()
    return time() - start


@pytest.mark.asyncio
class TestForce:

    async def test_forcing_objects_without_deferreds_does_nothing(self):
        obj = {"a": 1, "b": 2}
        await force(obj)
        assert obj == {"a": 1, "b": 2}

    async def test_replaces_deferreds_by_values_in_dict(self):
        obj = {"a": Box(1), "b": Box(2)}
        await force(obj)
        assert obj == {"a": 1, "b": 2}

    async def test_replaces_deferreds_by_values_in_list(self):
        obj = [Box(1), Box(2)]
        await force(obj)
        assert obj == [1, 2]

    async def test_replaces_deferreds_by_values_in_layered_object(self):
        obj = {"a": [Box(1), Box(2)], "b": {"c": Box(3)}}
        await force(obj)
        assert obj == {"a": [1, 2], "b": {"c": 3}}

    async def test_resolves_deferreds_concurrently(self):
        obj = {"a": Wait(1, delay=1), "b": Wait(2, delay=1)}
        elapsed = await measure(lambda: force(obj))
        assert obj == {"a": 1, "b": 2}
        assert elapsed < 1.1

    async def test_resolves_nested_deferreds_by_default(self):
        obj = {"a": Box(Box(1))}
        elapsed = await measure(lambda: force(obj))
        assert obj == {"a": 1}

    async def test_does_not_resolve_nested_deferreds_when_asked(self):
        deferred = Box(1)
        obj = {"a": Box(deferred)}
        elapsed = await measure(lambda: force(obj, deep=False))
        assert obj == {"a": deferred}
