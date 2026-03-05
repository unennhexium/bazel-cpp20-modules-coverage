from __future__ import annotations

import logging
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import machineid  # type: ignore[import-not-found]

from tool.arg.parse import parse_arguments
from tool.arg.prep import Arguments
from tool.lib.deco import time, trace
from tool.log.logger import init, logger
from tool.proc.filter import filter_, reset_cache
from tool.proc.gather import gather
from tool.proc.submit import submit

if TYPE_CHECKING:
    from pathlib import Path


def main():
    log_levels = {k: v for k, v in logging.__dict__.items() if k.isupper()}
    args = Arguments(parse_arguments(log_levels))
    init(args)
    logger.info("python:%s", sys.executable)
    logger.info("version:%s", sys.version)
    logger.info("argv:%s", sys.argv)
    process(args)
    # We need to reset cache in case "filter" module was
    # loaded once, then "filter_" is runing multiple times,
    # e.g. in tests.
    reset_cache()


def process(args: Arguments) -> None:
    paths = args.path
    ios = list(zip(paths.in_, paths.out_, strict=False))

    seed = machineid.hashed_id(sys.argv[0], winregistry=False)
    logger.info("machine+app seed:%s", f"{seed=}")
    random.seed(seed)

    def mapper(i: Path, o: Path) -> None:
        filter_(i, o, args, cache_stdin=True)

    is_py_3_13_or_above = sys.version_info >= (3, 13, 0)
    logger.info("GIL:%s", is_py_3_13_or_above and sys._is_gil_enabled())  # noqa: SLF001

    # There are one thread for each io pair + three nested std{in,out,err} for each.
    if is_py_3_13_or_above:
        max_workers = min(32, (os.process_cpu_count() or 1) + 4)
    else:
        max_workers = min(32, (os.cpu_count() or 1) + 4)
    max_workers = min(max_workers, len(paths.in_))
    logger.info("bound on number of workers:%s", f"{max_workers=}")

    with ThreadPoolExecutor(max_workers=max_workers) as extor:
        random.shuffle(ios)
        ti = (
            time(colored=args.log.color)  # Keep wrapped.
            if args.raw.time
            else (lambda f: f)
        )
        tr = (
            trace(args.raw.filter, colored=args.log.color)
            if args.raw.mem
            else (lambda f: f)
        )
        tr(ti(lambda: gather(submit(extor, ios, mapper))))()


if __name__ == "__main__":
    main()
