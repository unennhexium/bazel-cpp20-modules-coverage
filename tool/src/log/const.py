from __future__ import annotations

from enum import Enum, Flag, auto
from typing import NamedTuple, Self

type ColorMap[T] = dict[T, Color | list[Color]]


class Field(Enum):
    ASCTIME = "asctime"
    CREATED = "created"
    FILENAME = "filename"
    FUNCNAME = "funcName"
    LEVELNAME = "levelname"
    LEVELNO = "levelno"
    LINENO = "lineno"
    MESSAGE = "message"
    MODULE = "module"
    MSECS = "msecs"
    NAME = "name"
    PATHNAME = "pathname"
    PROCESS = "process"
    PROCESSNAME = "processName"
    RELATIVECREATED = "relativeCreated"
    THREAD = "thread"
    THREADNAME = "threadName"
    TASKNAME = "taskName"


class Level(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class ColorCode(NamedTuple):
    tens: int
    ones: int

    def __str__(self) -> str:
        return f"\33[{self.tens * 10 + self.ones}m"


class Color(Flag):
    @staticmethod
    def _generate_next_value_(
        _name: str,
        _start: int,
        count: int,
        last_values: list[tuple[int, int]],
    ) -> tuple[int, int]:
        tens, ones = last_values[count - 1]
        return tens, ones + 1

    def __new__(cls: type[Self], tens: int, ones: int) -> Self:
        obj: Color = object.__new__(cls)
        obj._value_ = 1 << len(cls.__members__)
        obj.cc = ColorCode(tens, ones)  # type: ignore[attr-defined]
        return obj

    def __str__(self) -> str:
        if len(self) > 1:
            return "".join(str(c.cc) for c in self)  # type: ignore[attr-defined]
        return str(self.cc)  # type: ignore[attr-defined]

    RESET = 0, 0

    BOLD = auto()
    DIM = auto()
    ITALIC = auto()
    UNDER_LINE = auto()
    BLINK = auto()
    INVERSE = auto()
    HIDDEN = auto()
    STRIKE_THROUGH = auto()

    OFF_BOLD = 2, 1
    OFF_DIM = auto()
    OFF_ITALIC = auto()
    OFF_UNDERLINE = auto()
    OFF_BLINK = auto()
    OFF_INVERSE = auto()
    OFF_HIDDEN = auto()
    OFF_STRIKE_THROUGH = auto()

    BLACK = 3, 0
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    MAGENTA = auto()
    CYAN = auto()
    WHITE = auto()

    DEFAULT = 3, 9

    BG_BLACK = 4, 0
    BG_RED = auto()
    BG_GREEN = auto()
    BG_YELLOW = auto()
    BG_BLUE = auto()
    BG_MAGENTA = auto()
    BG_CYAN = auto()
    BG_WHITE = auto()

    BG_DEFAULT = 4, 9

    BRIGHT_BLACK = 9, 0
    BRIGHT_RED = auto()
    BRIGHT_GREEN = auto()
    BRIGHT_YELLOW = auto()
    BRIGHT_BLUE = auto()
    BRIGHT_MAGENTA = auto()
    BRIGHT_CYAN = auto()
    BRIGHT_WHITE = auto()

    BG_BRIGHT_BLACK = 10, 0
    BG_BRIGHT_RED = auto()
    BG_BRIGHT_GREEN = auto()
    BG_BRIGHT_YELLOW = auto()
    BG_BRIGHT_BLUE = auto()
    BG_BRIGHT_MAGENTA = auto()
    BG_BRIGHT_CYAN = auto()
    BG_BRIGHT_WHITE = auto()
