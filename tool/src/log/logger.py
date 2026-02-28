from __future__ import annotations

from logging import StreamHandler, getLogger
from typing import TYPE_CHECKING

from src.log.const import Field
from src.log.fmt import Formatter

if TYPE_CHECKING:
    from src.arg.prep import Arguments


logger = getLogger(__name__)


def init(args: Arguments) -> None:
    logger.setLevel(args.log.level)
    handler = StreamHandler()
    logger.addHandler(handler)
    fields = [
        Field.LEVELNAME,
        Field.THREADNAME,
        Field.MODULE,
        Field.LINENO,
        Field.FUNCNAME,
        Field.MESSAGE,
    ]
    formatter = Formatter(fields, colored=args.log.color, width=args.log.width)
    handler.setFormatter(formatter)
