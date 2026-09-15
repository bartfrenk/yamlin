from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import sleep
from collections.abc import Coroutine
from logging import getLogger
from os import environ
from typing import IO, Generic, TypeVar, final, override

from keyring import get_password
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
        add_constructor("!keychain", KeychainResolver("!keychain"), Loader=ConfigLoader)
        add_constructor("!env", EnvResolver("!env"), Loader=ConfigLoader)


class Resolver(ABC, Generic[T]):
    def __call__(self, loader: ConfigLoader, node: Node) -> Coroutine[object, object, T]:
        return self.resolve(loader, node)

    @abstractmethod
    async def resolve(self, loader: ConfigLoader, node: Node) -> T: ...


class SleepResolver(Resolver[int]):
    def __init__(self, tag: str) -> None:
        self.tag: str = tag

    @override
    async def resolve(self, loader: ConfigLoader, node: Node) -> int:
        assert isinstance(node, ScalarNode)
        n = loader.construct_yaml_int(node)
        await sleep(n)
        return n


class KeychainResolver(Resolver[str]):
    def __init__(self, tag: str) -> None:
        self.tag: str = tag

    @override
    async def resolve(self, loader: ConfigLoader, node: Node) -> str:
        assert isinstance(node, ScalarNode)
        value = loader.construct_scalar(node)
        service, sep, identifier = value.partition("/")
        if not sep:
            raise YamlinError(self.tag, f"expected <service>/<secret id>, got {value!r}")
        password = get_password(service, identifier)
        if password is None:
            raise YamlinError(self.tag, f"no keychain entry found for {value!r}")
        return password


class EnvResolver(Resolver[str]):
    def __init__(self, tag: str) -> None:
        self.tag: str = tag

    @override
    async def resolve(self, loader: ConfigLoader, node: Node) -> str:
        assert isinstance(node, ScalarNode)
        name = loader.construct_scalar(node)
        value = environ.get(name)
        if value is None:
            raise YamlinError(self.tag, f"environment variable {name!r} is not set")
        return value
