from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from tool.arg.action import Action
from tool.lib.util import is_list_wo_none

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence


class PathIn(Action):
    def __init__(self, option_strings, **kwargs):
        self.paths = []
        super().__init__(option_strings, **kwargs)

    def prepare(self, option_arguments: Sequence[str], **_kwargs) -> list[Path]:
        paths = option_arguments
        res = cast("list[Path | None]", [None]) * len(paths)
        for ind, pth in enumerate(paths):
            if str(pth) == "-":
                res[ind] = Path("/dev/stdin")
            else:
                res[ind] = Path(pth)
        assert is_list_wo_none(res)  # noqa: S101
        self.paths.extend(res)
        return self.paths


class PathOut(Action):
    def __init__(self, option_strings, **kwargs):
        self.paths = []
        super().__init__(option_strings, **kwargs)

    def prepare(
        self,
        option_arguments: Sequence[str],
        *,
        namespace: Namespace,
        **_kwargs,
    ) -> list[Path]:
        paths = option_arguments
        if namespace.test:
            return [Path("/dev/null")] * len(namespace.input)
        if len(paths) == 1 and str(paths[0]) == "-":
            return [Path("/dev/stdout")] * len(namespace.input)
        res = cast("list[Path | None]", [None]) * len(paths)
        for ind, pth in enumerate(paths):
            if str(pth) == "-":
                res[ind] = Path("/dev/stdout")
            else:
                res[ind] = Path(pth)
        assert is_list_wo_none(res)  # noqa: S101
        self.paths.extend(res)
        return self.paths
