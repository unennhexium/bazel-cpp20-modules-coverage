from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard

from more_itertools import windowed  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


type LineFilter = Callable[[Iterator[str], *Any], Iterator[str]]


def dummy(stream: Iterator[str], *_rest: Any) -> Iterator[str]:
    yield from stream


def window[T](itor: Iterator[T], size=2, step=1) -> Iterator[tuple[T, T]]:
    for tup in windowed(itor, n=size, step=step):
        assert is_non_none_tuple(tup)  # noqa: S101
        yield tup


def is_non_none_tuple[T](tup: tuple[T | None, ...]) -> TypeGuard[tuple[T, ...]]:
    return all((it is not None) for it in tup)


def select[T](itor: Iterator[T], ranges: list[tuple[int, int]]) -> Iterator[T]:
    for ind, line in enumerate(itor):
        for up, down in ranges:
            if down < ind < up:
                yield line
