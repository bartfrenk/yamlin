from asyncio import sleep
from time import time
from typing import Any, Tuple, TypeVar

import pytest

from yamlin.deferred import gather
from yamlin.utils import measure

T = TypeVar("T")


async def with_delay(delay: int, result: T) -> T:
    await sleep(delay)
    return result


async def box(value: T) -> T:
    return value


async def wait(value: T, *, delay: int = 1) -> T:
    await sleep(delay)
    return value


@pytest.mark.asyncio
class TestGather:

    async def test_gathering_object_without_coroutines_does_nothing(self):
        obj = {"a": 1, "b": 2}
        await gather(obj)
        assert obj == {"a": 1, "b": 2}

    async def test_replaces_coroutines_by_values_in_dict(self):
        obj = {"a": box(1), "b": box(2)}
        await gather(obj)
        assert obj == {"a": 1, "b": 2}

    async def test_replaces_coroutines_by_values_in_list(self):
        obj = [box(1), box(2)]
        await gather(obj)
        assert obj == [1, 2]

    async def test_replaces_coroutines_by_values_in_layered_object(self):
        obj = {"a": [box(1), box(2)], "b": {"c": box(3)}}
        await gather(obj)
        assert obj == {"a": [1, 2], "b": {"c": 3}}

    async def test_resolves_coroutines_concurrently(self):
        obj = {"a": wait(1, delay=1), "b": wait(2, delay=1)}
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": 1, "b": 2}
        assert elapsed < 1.1

    async def test_resolves_nested_coroutines_by_default(self):
        obj = {"a": box(box(1))}
        elapsed = await measure(lambda: gather(obj))
        assert obj == {"a": 1}

    async def test_does_not_resolve_nested_coroutines_when_asked(self):
        deferred = box(1)
        obj = {"a": box(deferred)}
        elapsed, _ = await measure(lambda: gather(obj, deep=False))
        assert obj == {"a": deferred}

    async def test_resolve_coroutines_to_values(self):
        obj = {"a": with_delay(1, 1), "b": with_delay(1, 2)}
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": 1, "b": 2}
        assert elapsed < 1.1

    async def test_resolves_lists_of_coroutines(self):
        obj = {"a": [with_delay(1, 1), with_delay(1, 2)]}
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": [1, 2]}
        assert elapsed < 1.1

    async def test_resolves_nested_structures(self):
        obj = {"a": [with_delay(1, 1), {"b": with_delay(1, 2)}]}
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": [1, {"b": 2}]}
        assert elapsed < 1.1

    async def test_resolves_nested_coroutines(self):
        obj = {"a": with_delay(1, with_delay(1, 1))}
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": 1}
        assert elapsed < 2.1

    @pytest.mark.skip(reason="This tests desired behavior that is not implemented yet.")
    async def test_does_not_resolve_per_layer(self):
        obj = {
            "a": with_delay(2, 1),
            "b": with_delay(1, [with_delay(1, 2), with_delay(1, 3)]),
        }
        elapsed, _ = await measure(lambda: gather(obj))
        assert obj == {"a": 1, "b": [2, 3]}
        assert elapsed < 2.1
