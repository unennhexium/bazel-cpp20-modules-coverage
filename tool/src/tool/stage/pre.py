from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tool.line.delimiters import COMMENT, MARKER
from tool.log.logger import logger

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator


def pre(stream: Iterator[str], rgx: re.Pattern) -> Iterator[str]:
    for line in stream:
        if rgx.match(line):
            logger.debug("%s", f"{line=}")
            rnd = random.randint(0, 999_999)  # noqa: S311
            logger.debug("%s", f"{rnd=}")
            yield f"{MARKER.open}{rnd}{MARKER.close}"
            yield f"{COMMENT.open}{rnd}{line.rstrip()}{COMMENT.close}"
        else:
            yield line
