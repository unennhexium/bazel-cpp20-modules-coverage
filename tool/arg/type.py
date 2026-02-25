from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from tool.lib.gen import LineFilter


class Width(Enum):
    ALWAYS = 0
    NEVER = 1
    CUSTOM = 2


class Paths(NamedTuple):
    in_: list[Path]
    out_: list[Path]


class Stages(NamedTuple):
    pre: LineFilter
    mid: LineFilter
    post: LineFilter


class Log(NamedTuple):
    level: int
    width: tuple[Width, int]
    color: bool
