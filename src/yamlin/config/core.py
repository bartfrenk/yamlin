from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import sleep
from collections.abc import Coroutine
from logging import getLogger
from typing import IO, Generic, TypeVar, final

from yaml import Node, SafeLoader, ScalarNode, add_constructor

log = getLogger(__name__)

T = TypeVar("T")

_ReadStream = str | bytes | IO[str] | IO[bytes]


@final
class YamlinError(Exception):
    def __init__(self, tag: str, message: str) -> None:
        super().__init__(f"{message} [{tag}]")
        self.tag = tag
        self.message = message


class ConfigLoader(SafeLoader):
    def __init__(self, stream: _ReadStream) -> None:
        super().__init__(stream)
        add_constructor("!sleep", SleepResolver("!sleep"), Loader=ConfigLoader)


class Resolver(ABC, Generic[T]):
    def __call__(
        self, loader: ConfigLoader, node: Node
    ) -> Coroutine[object, object, T]:
        return self.resolve(loader, node)

    @abstractmethod
    async def resolve(self, loader: ConfigLoader, node: Node) -> T: ...


class SleepResolver(Resolver[int]):
    def __init__(self, tag: str) -> None:
        self.tag: str = tag

    async def resolve(  # pyright: ignore[reportImplicitOverride]
        self, loader: ConfigLoader, node: Node
    ) -> int:
        assert isinstance(node, ScalarNode)
        n = loader.construct_yaml_int(node)
        await sleep(n)
        return n
