from __future__ import annotations

import logging
import os
import sys
from argparse import ArgumentError
from typing import TYPE_CHECKING

from tool.arg.action import Action

if TYPE_CHECKING:
    from collections.abc import Sequence


def level(log_levels: dict[str, int]):
    class Level(Action):
        def prepare(self, option_arguments: Sequence[str], **_kwargs) -> int:  # noqa: PLR6301
            args = option_arguments
            if (ll := os.getenv("TOOL_LOG_LEVEL")) is not None:
                if len(ll) == 0:
                    return logging.DEBUG
                if (ll_int := log_levels.get(ll)) is not None:
                    return ll_int
                msg = (
                    "Invalid LOG_LEVEL environment variable value. "
                    f"Possible values: {log_levels.keys()}"
                )
                raise ArgumentError(None, msg)
            return args.log

    return Level


class Color(Action):
    def prepare(self: Color | None, option_arguments: Sequence[str], **_kwargs) -> bool:  # noqa: PLR6301
        if (cl := os.getenv("TOOL_COLOR")) is not None:
            match cl:
                case "auto":
                    return sys.stderr.isatty()
                case "never" | "":
                    return False
                case "always":
                    return True
                case _:
                    msg = "Non-exhaustive `match` statement."
                    raise RuntimeError(msg)
        if option_arguments == "auto":
            return sys.stderr.isatty()
        return option_arguments == "always"
