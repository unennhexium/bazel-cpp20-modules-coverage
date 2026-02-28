from __future__ import annotations

from typing import TYPE_CHECKING

from src.lib.popen import PopenContext
from src.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.arg.prep import Arguments


def mid(stream: Iterator[str], args: Arguments) -> Iterator[str]:
    with PopenContext(
        args.cmd,
        shell=len(args.cmd) == 1,
        size=args.raw.queue,
        poll=args.raw.poll,
        timeout=args.raw.timeout,
    ) as (
        q_in,
        q_out,
        _,
    ):
        try:
            for line in stream:
                q_in.put(line)
            q_in.put(PopenContext.EOF)
            for line in iter(q_out.get, PopenContext.EOF):  # type: ignore[assignment]
                yield line
                q_out.task_done()
            q_out.task_done()
            logger.debug("finished `yield`ing")
            for q, n in zip((q_in, q_out), ("in", "out"), strict=False):
                logger.debug("'%s' queue approximate size:%d", n, q.qsize())
                q.join()
                logger.debug("a queue '%s' has joined", n)
        except GeneratorExit:
            logger.debug("exiting generator")
