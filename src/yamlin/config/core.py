from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import run, sleep
from logging import getLogger

import yaml
from yaml import Node, SafeLoader, add_constructor

log = getLogger(__name__)


class YamlinError(Exception):
    def __init__(self, tag: str, message: str) -> None:
        super().__init__(f"{message} [{tag}]")
        self.tag = tag
        self.message = message


class ConfigLoader(SafeLoader):
    def __init__(self, stream) -> None:
        super().__init__(stream)
        add_constructor("!sleep", SleepResolver("!sleep"), Loader=ConfigLoader)


class Resolver(ABC):
    def __call__(self, loader, node: Node):
        return self.resolve(loader, node)

    @abstractmethod
    async def resolve(self, loader, node: Node): ...


class SleepResolver(Resolver):
    def __init__(self, tag: str):
        self.tag = tag

    async def resolve(self, loader, node: Node):
        n = loader.construct_yaml_int(node)
        await sleep(n)
        return n
