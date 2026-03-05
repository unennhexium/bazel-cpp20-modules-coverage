from __future__ import annotations

from typing import NamedTuple

from tool.line.line import Line


class Delimiter(NamedTuple):
    open: str
    middle: str | None
    close: str


MARKER = Delimiter("int ", None, ";\n")
COMMENT = Delimiter("/* ", "#", " */\n")


class Marker(Line):
    def __init__(self, marker: str) -> None:
        super().__init__(marker, MARKER.open, MARKER.close)


class Pragma(Line):
    def __init__(self, pragma: str) -> None:
        super().__init__(pragma, COMMENT.open, COMMENT.close, COMMENT.middle)
