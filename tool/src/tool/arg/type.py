import re
from functools import update_wrapper, wraps
from pathlib import Path as PyPath
from typing import NamedTuple

from tool.lib.gen import LineFilter


class PathRepr(PyPath):
    def __repr__(self) -> str:
        return self.as_posix()


class Wrapper:
    def __init__(self, repr_, func):
        self._repr = repr_
        self._func = func
        update_wrapper(self, func)

    def __call__(self, *args, **kw):
        return self._func(*args, **kw)

    def __repr__(self):
        return self._repr(self._func)


def with_repr(fun):
    @wraps(fun)
    def _with_repr(func):
        return Wrapper(fun, func)

    return _with_repr


class Stage(NamedTuple):
    pre: LineFilter
    mid: LineFilter
    post: LineFilter


class Select(NamedTuple):
    pat: list[re.Pattern]
    rng: list[tuple[int, int]]


class Path(NamedTuple):
    in_: list[PyPath]
    out_: list[PyPath]


class Log(NamedTuple):
    level: int
    width: int
    color: bool
