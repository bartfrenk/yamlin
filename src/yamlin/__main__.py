import sys
from argparse import ArgumentParser
from asyncio import run
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

import yaml

from yamlin.facade import read_stream


def parse_args() -> tuple[Path | None, Path | None]:
    parser = ArgumentParser(description="Resolve a YAML config.")
    parser.add_argument("-f", "--file", type=Path, help="input file (default: stdin)")
    parser.add_argument("-o", "--output", type=Path, help="output file (default: stdout)")
    args = parser.parse_args()
    return args.file, args.output  # pyright: ignore[reportAny]


@contextmanager
def open_stream(path: Path | None, *, fallback: IO[str]) -> Generator[IO[str], object, object]:
    if path:
        with open(path) as stream:
            yield stream
    else:
        yield fallback


def main() -> None:
    input_path, output_path = parse_args()
    with open_stream(input_path, fallback=sys.stdin) as stream:
        obj = run(read_stream(stream))

    result = yaml.dump(obj)

    with open_stream(output_path, fallback=sys.stdout) as stream:
        stream.write(result)


if __name__ == "__main__":
    main()
