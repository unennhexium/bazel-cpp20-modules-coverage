from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tool.lib.util import plural
from tool.log.logger import logger
from tool.proc.io import IO

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Future, ThreadPoolExecutor
    from pathlib import Path


def submit(
    extor: ThreadPoolExecutor,
    ios: list[IO],
    mapper: Callable[[Path, Path], None],
) -> dict[Future, IO]:
    futures = {}
    random.shuffle(ios)
    for ind, io in enumerate(ios):
        i, o = (p.as_posix() for p in io)
        logger.info(
            "%d file%s sumbitted: %s -> %s",
            ind + 1,
            plural(ind),
            i,
            o,
        )
        futures[extor.submit(mapper, *io)] = io
    return futures
