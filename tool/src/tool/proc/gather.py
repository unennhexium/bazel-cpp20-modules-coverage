from __future__ import annotations

from concurrent.futures import Future, as_completed

from tool.lib.util import plural
from tool.log.logger import logger
from tool.proc.io import IO


def gather(futures: dict[Future, IO]) -> None:
    for ind, future in enumerate(as_completed(futures)):
        i, o = (p.as_posix() for p in futures[future])
        _ = future.result()
        logger.info(
            "%d file%s processed: %s -> %s",
            ind + 1,
            plural(ind),
            i,
            o,
        )
