import sys
from argparse import ArgumentParser
from asyncio import run

import yaml

from yamlin.config.core import ConfigLoader
from yamlin.tasks import gather


async def resolve(text: str) -> str:
    obj = yaml.load(text, Loader=ConfigLoader)  # pyright: ignore[reportAny]
    await gather(obj)  # pyright: ignore[reportAny]
    return yaml.dump(obj)


def parse_args() -> tuple[str | None, str | None]:
    parser = ArgumentParser(description="Resolve a YAML config.")
    parser.add_argument("-f", "--file", help="input file (default: stdin)")
    parser.add_argument("-o", "--output", help="output file (default: stdout)")
    args = parser.parse_args()
    return args.file, args.output  # pyright: ignore[reportAny]


def main() -> None:
    input_path, output_path = parse_args()
    if input_path:
        with open(input_path) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = run(resolve(text))

    if output_path:
        with open(output_path, "w") as f:
            f.write(result)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
