from __future__ import annotations

from typing import TYPE_CHECKING

from src.lib.gen import select
from src.lib.util import plural
from src.log.logger import logger

if TYPE_CHECKING:
    import re
    from pathlib import Path

    from src.arg.prep import Arguments


def filter_(
    path_in: Path,
    path_out: Path,
    args: Arguments,
    re: re.Pattern,
) -> None:
    logger.info("start filtering: %s -> %s", path_in.as_posix(), path_out.as_posix())
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
            in_itor = select(file_in, args.raw.range)
        res_itor = args.stages.pre(in_itor, re)
        res_itor = args.stages.mid(res_itor, args)
        res_itor = args.stages.post(res_itor)
        for ind, line in enumerate(res_itor):
            file_out.write(line)
            logger.debug("%d line%s recieved", ind + 1, plural(ind))
    logger.info("end filtering: %s -> %s", path_in.as_posix(), path_out.as_posix())
