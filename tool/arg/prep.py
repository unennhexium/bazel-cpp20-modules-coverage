from __future__ import annotations

import logging
import sys
from argparse import (
    ArgumentError,
    Namespace,
)
from os import environ as env
from pathlib import Path
from shutil import which
from typing import cast

from tool.arg.type import Log, Paths, Stages, Width
from tool.lib.gen import LineFilter, dummy
from tool.lib.util import is_list_wo_none
from tool.stage.mid import mid
from tool.stage.post import post
from tool.stage.pre import pre


class Arguments:
    def __init__(self, args: Namespace, log_levels: dict[str, int]) -> None:
        self.raw = args
        self.stages = Stages(*self._stages())
        self.cmd = self._cmd()
        self.paths = Paths(
            self._paths_in(args.input),
            self._paths_out(args.out),
        )
        self.log = Log(
            self._log_level(log_levels),
            self._log_width(),
            self._log_color(),
        )

    def _stages(self) -> tuple[LineFilter, LineFilter, LineFilter]:
        args = self.raw
        full = "full" in args.stage
        return (  # type: ignore[assignment]
            pre if full or "pre" in args.stage else dummy,
            mid if full or "mid" in args.stage else dummy,
            post if full or "post" in args.stage else dummy,
        )

    def _paths_in(self, paths: list[Path]) -> list[Path]:
        _ = self
        cnt = 0
        res = cast("list[Path | None]", [None]) * len(paths)
        for ind, pth in enumerate(paths):
            if str(pth) == "-":
                res[ind] = Path("/dev/stdin")
                cnt += 1
            else:
                res[ind] = pth
        if cnt > 1:
            msg = "Stdin ('-') can be processed only once."
            raise ArgumentError(None, msg)
        assert is_list_wo_none(res)  # noqa: S101
        return res

    def _paths_out(self, paths: list[Path] | None) -> list[Path]:
        args = self.raw
        if args.test:
            return [Path("/dev/null")] * len(args.input)
        if paths is None or (len(paths) == 1 and str(paths) == "-"):
            return [Path("/dev/stdout")] * len(args.input)
        res = cast("list[Path | None]", [None]) * len(paths)
        for ind, pth in enumerate(paths):
            if str(pth) == "-":
                res[ind] = Path("/dev/stdout")
            else:
                res[ind] = pth
        assert is_list_wo_none(res)  # noqa: S101
        return res

    def _cmd(self) -> list[str]:
        if self.raw.script is not None:
            return [self.raw.script]
        cmd = [
            self._clang_path().as_posix(),
            "-E",
            "-P",
            *self._clang_args(),
            "-",
        ]
        buff = self._clang_buff()
        if len(buff) != 0:
            return [*buff, "--", *cmd]
        return cmd

    def _clang_args(self) -> list[str]:
        args = self.raw
        clang_args: list[str] = []
        if args.clang is not None:
            clang_args.extend(a.lstrip("\\") for a in args.clang)
        if args.define is not None:
            clang_args.extend("-D" + d for d in args.define)
        if args.keep:
            clang_args.append("-C")
        return clang_args

    def _clang_buff(self) -> list[str]:
        args = self.raw
        opts: list[str] = []
        for arg, io in zip((args.ibuff, args.obuff), ("i", "o"), strict=False):
            Arguments._buff_arg(opts, arg, io)
        stdbuf = which("stdbuf")
        if stdbuf is None:
            msg = "stdbuf is not found in $PATH."
            raise RuntimeError(msg)
        return [] if len(opts) == 0 else [stdbuf[0], *opts]

    @staticmethod
    def _buff_arg(opts: list[str], arg: str, io: str) -> None:
        match arg:
            case "def":
                pass
            case "line":
                if io == "i":
                    raise ArgumentError(None, "Line buffered stdin is meaningless.")
                opts.append(f"-{io}L")
            case "zero":
                opts.append(f"-{io}0")
            case _:
                msg = "Non-exhaustive `match` statement."
                raise RuntimeError(msg)

    def _clang_path(self) -> Path:
        args = self.raw
        if args.path is None:
            path = which("clang")
            if path is None:
                msg = (
                    "clang is not found in $PATH. "
                    "Specify the path to clang executable. "
                    "See -h,--help."
                )
                raise RuntimeError(msg)
            clang = Path(path)
        else:
            clang = args.path.absolute()
        return clang

    def _log_level(self, levels: dict[str, int]) -> int:
        args = self.raw
        if args.log is None:
            return logging.WARNING
        if (ll := env.get("LOG_LEVEL")) is not None:
            if len(ll) == 0:
                return logging.WARNING
            if (ll_int := levels.get(ll)) is not None:
                return ll_int
            msg = (
                "Invalid LOG_LEVEL environment veriable value. "
                f"Possible values: {levels.keys()}"
            )
            raise ArgumentError(None, msg)
        return logging.WARNING

    def _log_width(self) -> tuple[Width, int]:
        args = self.raw
        if args.truncate is None:
            return Width.ALWAYS, 0
        match args.truncate:
            case "always":
                return Width.ALWAYS, 0
            case "never":
                return Width.NEVER, -1
            case "custom":
                if args.width is None:
                    raise ArgumentError(None, "Truncation width should be specified.")
                return Width.CUSTOM, args.width
            case _:
                msg = "Non-exhaustive `match` statement."
                raise RuntimeError(msg)

    def _log_color(self) -> bool:
        args = self.raw
        if args.color is None or args.color == "auto":
            return sys.stderr.isatty()
        return args.color == "always"
