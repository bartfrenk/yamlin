import sys
from asyncio import run

import yaml

from yamlin.config.core import ConfigLoader
from yamlin.tasks import gather


async def resolve(text: str) -> str:
    obj = yaml.load(text, Loader=ConfigLoader)  # pyright: ignore[reportAny]
    await gather(obj)  # pyright: ignore[reportAny]
    return yaml.dump(obj)


def main() -> None:
    sys.stdout.write(run(resolve(sys.stdin.read())))


if __name__ == "__main__":
    main()
