from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tool.arg.type import with_repr
from tool.line.delimiter import COMMENT, MARKER
from tool.log.logger import logger

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator


@with_repr(lambda f: f.__name__)
def pre(stream: Iterator[str], rgx: list[re.Pattern]) -> Iterator[str]:
    for line in stream:
        if any(r.match(line) for r in rgx):
            logger.debug("%s", f"{line=}")
            rnd = random.randint(0, 999_999)  # noqa: S311
            logger.debug("%s", f"{rnd=}")
            yield f"{MARKER.open}{rnd}{MARKER.close}"
            yield f"{COMMENT.open}{rnd}{line.rstrip()}{COMMENT.close}"
        else:
            yield line
