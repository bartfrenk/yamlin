from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import Task, create_task, gather, run, sleep
from dataclasses import dataclass
from logging import getLogger

import yaml
from yaml import Loader, Node, SafeLoader, add_constructor

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


@dataclass
class Deferred:
    resolver: Resolver
    node: Node
    loader: Loader

    async def get(self):
        return await self.resolver.resolve(self.loader, self.node)


class Resolver(ABC):
    def __call__(self, loader, node: Node):
        return Deferred(node=node, resolver=self, loader=loader)

    @abstractmethod
    async def resolve(self, loader, node: Node): ...


class SleepResolver(Resolver):
    def __init__(self, tag: str):
        self.tag = tag

    async def resolve(self, loader, node: Node):
        n = loader.construct_yaml_int(node)
        await sleep(n)
        return n


async def force(obj):

    async def recur(tasks, obj):
        match obj:
            case Deferred(resolver=resolver, node=node, loader=loader):
                task = create_task(resolver.resolve(loader, node))
                tasks.append(task)
                return task
            case dict():
                for k, v in obj.items():
                    obj[k] = await recur(tasks, v)
                return obj
            case list():
                for i, v in enumerate(obj):
                    obj[i] = await recur(tasks, v)
                return obj

    tasks = []
    result = await recur(tasks, obj)
    print(tasks)
    await gather(*tasks)
    return result


def result(obj):

    def recur(obj):
        match obj:
            case Task():
                return obj.result()
            case dict():
                for k, v in obj.items():
                    obj[k] = recur(v)
                return obj
            case list():
                for i, v in enumerate(obj):
                    obj[i] = recur(v)
                return obj

    return recur(obj)


async def main():
    import devtools

    with open("config.yaml") as f:
        obj = yaml.load(f, Loader=ConfigLoader)
        devtools.pprint(obj)
        print(result(await force(obj)))


if __name__ == "__main__":
    run(main())
