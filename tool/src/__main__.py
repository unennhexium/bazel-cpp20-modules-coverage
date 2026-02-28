from __future__ import annotations

import logging
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import machineid  # type: ignore[import-not-found]
from src.arg.parse import parse_arguments
from src.arg.prep import Arguments
from src.lib.deco import time, trace
from src.log.logger import init, logger
from src.proc.filter import filter_
from src.proc.gather import gather
from src.proc.submmit import submit

if TYPE_CHECKING:
    from pathlib import Path


def main():
    log_levels = {k: v for k, v in logging.__dict__.items() if k.isupper()}
    args = Arguments(parse_arguments(log_levels), log_levels)
    init(args)
    logger.info("python:%s", sys.executable)
    logger.info("version:%s", sys.version)
    logger.info("argv:%s", sys.argv)
    process(args)


def process(args: Arguments) -> None:
    paths = args.paths
    ios = list(zip(paths.in_, paths.out_, strict=False))

    seed = machineid.hashed_id(sys.argv[0], winregistry=False)
    logger.info("machine+app seed:%s", f"{seed=}")
    random.seed(seed)

    rgx = re.compile(r"#[ \t]*include[ \t]+.*")

    def mapper(i: Path, o: Path) -> None:
        filter_(i, o, args, rgx)

    is_py_3_13_or_above = sys.version_info >= (3, 13, 0)
    logger.info("GIL:%s", is_py_3_13_or_above and sys._is_gil_enabled())  # noqa: SLF001

    # There are one thread for each io pair + three nested std{in,out,err} for each.
    if is_py_3_13_or_above:
        max_workers = min(32, (os.process_cpu_count() or 1) + 4)
    else:
        max_workers = min(32, (os.cpu_count()) + 4)
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
