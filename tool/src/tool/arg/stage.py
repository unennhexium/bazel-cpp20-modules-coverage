from __future__ import annotations

from typing import TYPE_CHECKING

from tool.arg.action import Action
from tool.lib.gen import LineFilter, dummy
from tool.stage.mid import mid
from tool.stage.post import post
from tool.stage.pre import pre

if TYPE_CHECKING:
    from collections.abc import Sequence


class Stage(Action):
    @staticmethod
    def prepare(
        option_arguments: Sequence[str],
        **_kwargs,
    ) -> tuple[LineFilter, LineFilter, LineFilter]:
        args = option_arguments
        full = "all" in args
        not_none = "none" not in args
        return tuple(
            f if (full or f.__name__ in args) and not_none else dummy
            for f in (pre, mid, post)
        )
