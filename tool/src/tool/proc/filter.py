from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from tool.lib.gen import select
from tool.lib.util import plural
from tool.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from tool.arg.prep import Arguments

STDIN_CACHE: list[str] | None = None
LOCK = Lock()


def reset_cache():
    global STDIN_CACHE  # noqa: PLW0603
    STDIN_CACHE = None


type Streamer = Callable[[Iterator[str]], Iterator[str]]


def cacher(streamer: Streamer) -> Streamer:
    global STDIN_CACHE  # noqa: PLW0602 # Global state coupled with `lock`.

    def _streamer(stream: Iterator[str]) -> Iterator[str]:
        for ind, line in enumerate(streamer(stream)):
            STDIN_CACHE.append(line)
            logger.debug("%d line%s saved into stdin cache", ind + 1, plural(ind))
            yield line

    return _streamer


def filter_(
    path_in: Path,
    path_out: Path,
    args: Arguments,
    *,
    cache_stdin: bool = True,
) -> None:
    global STDIN_CACHE  # noqa: PLW0603 # Global state coupled with `lock`.
    is_acquired = False
    stage_post = args.stages.post
    if cache_stdin and path_in.as_posix() == "/dev/stdin":
        logger.debug("checking stdin cache, acquire the lock")
        LOCK.acquire()
        is_acquired = True
        if STDIN_CACHE is None:
            logger.debug("stdin cache is empty, do filter and populate")
            STDIN_CACHE = []
            stage_post = cacher(stage_post)
        else:
            logger.debug("stdin cache already populated , write it out, do not filter")
            with path_out.open("w", encoding="utf-8") as file_out:
                file_out.writelines("".join(STDIN_CACHE))
            LOCK.release()
            return
    logger.debug("start filtering: %s -> %s", path_in.as_posix(), path_out.as_posix())
    if not path_out.exists():
        path_out.touch()
    with (
        path_in.open("r", encoding="utf-8") as file_in,
        path_out.open("w", encoding="utf-8") as file_out,
    ):
        logger.debug("%s", f"{path_in=}")
        in_itor = iter(file_in)

        def logger_(itor):
            for ind, line in enumerate(itor):
                logger.debug("%d line%s sent", ind + 1, plural(ind))
                yield line

        in_itor = logger_(in_itor)
        if args.raw.range is not None:
            in_itor = select(file_in, args.sels.rng)
        res_itor = args.stages.pre(in_itor, args.sels.pat)
        res_itor = args.stages.mid(res_itor, args)
        res_itor = stage_post(res_itor)
        for ind, line in enumerate(res_itor):
            file_out.write(line)
            logger.debug("%d line%s received", ind + 1, plural(ind))
    logger.info("end filtering: %s -> %s", path_in.as_posix(), path_out.as_posix())
    # We should check thread-local variable, since
    # the `lock` can be acquired by the other thread.
    if is_acquired:
        logger.debug("end caching stdin, release the lock")
        LOCK.release()
