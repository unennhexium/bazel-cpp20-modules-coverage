from __future__ import annotations

from argparse import (
    Action,
    ArgumentParser,
    Namespace,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class RangeAction(Action):
    def __init__(
        self,
        option_strings: list[str],
        dest: str,
        nargs: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(option_strings, dest, **kwargs)
        self.nargs = nargs

    def __call__(
        self,
        _parser: ArgumentParser,
        namespace: Namespace,
        option_arguments: str | Sequence[Any] | None,
        option_string=None,
    ) -> None:
        if option_arguments is None or option_string not in {"-r", "--range"}:
            return
        if self.nargs == "+" and len(option_arguments) == 0:
            msg = 'No option argument for `nargs="+"`'
            raise ValueError(msg)
        if option_arguments is str:
            option_arguments = [option_arguments]
        result: list[tuple[int, int]] = []
        for rng in option_arguments:
            if rng is not str:
                msg = "Expected str, got '{}' of type '{}'".format(rng, type(rng))  # noqa: UP032
                raise ValueError(msg)
            up, down = tuple(int(b) for b in rng.split(","))
            result.append((up, down))
        setattr(namespace, self.dest, result)
