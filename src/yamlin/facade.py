from pathlib import Path
from typing import IO

import yaml

from yamlin.config.core import ConfigLoader
from yamlin.tasks import Container, gather


async def read_stream(stream: IO[str]) -> Container:
    obj: Container = yaml.load(stream, Loader=ConfigLoader)  # pyright: ignore[reportAny]
    await gather(obj)
    return obj


async def read_file(path: Path) -> Container:
    with open(path) as stream:
        return await read_stream(stream)
