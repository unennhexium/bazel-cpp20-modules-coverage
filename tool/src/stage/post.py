from __future__ import annotations

from typing import TYPE_CHECKING

from src.lib.gen import window
from src.line.delimiters import Marker, Pragma
from src.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import Iterator


def post(stream: Iterator[str]) -> Iterator[str]:
    cur: str
    nxt: str
    skip = False
    for cur, nxt in window(stream):
        logger.debug("%-35s", f"{cur=}")
        logger.debug("%-35s", f"{nxt=}")
        logger.debug("%s", f"{skip=}")
        if skip:
            skip = False
            yield "\n"
            continue
        cur_marker = Marker(cur)
        nxt_pragma = Pragma(nxt)
        match cur_marker.id, nxt_pragma.id:
            case -1, -1:  # Both regular.
                logger.debug("case (1): both regular")
                yield cur  # `nxt` may be pragma.
            case _, -1:  # '-C' was provided to Clang, so no commented pragma kept.
                logger.debug("case (2): first is marker")
                yield ""
            case -1, _:  # Second is pragma but marker was removed.
                logger.debug("case (3): second pragma")
                yield ""
                skip = True
            case _, _:  # First is marker, second is pragma.
                logger.debug("case (4): first marker, second pragma")
                yield nxt_pragma.line  # Keep pragma.
                skip = True
    if not skip:  # Last line is regular.
        yield nxt
