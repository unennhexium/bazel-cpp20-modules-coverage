from argparse import ArgumentError, Namespace
from pathlib import Path
from shutil import which


class Cmd:
    def __init__(self, args: Namespace) -> None:
        self.args = args

    def build(self) -> list[str]:
        if self.args.script is not None:
            return [self.args.script]
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

    def _clang_path(self) -> Path:
        args = self.args
        if args.path is None:
            path = which("clang")
            if path is None:
                msg = (
                    "clang is not found in $PATH. "
                    "Provide the path to clang executable. "
                    "See -h,--help."
                )
                raise RuntimeError(msg)
            clang = Path(path)
        else:
            clang = args.path.absolute()
        return clang

    def _clang_args(self) -> list[str]:
        args = self.args
        clang_args: list[str] = []
        if args.clang is not None:
            clang_args.extend(a.lstrip("\\") for a in args.clang)
        if args.define is not None:
            clang_args.extend("-D" + d for d in args.define)
        if args.keep:
            clang_args.append("-C")
        return clang_args

    def _clang_buff(self) -> list[str]:
        args = self.args
        opts: list[str] = []
        for arg, io in zip((args.ibuff, args.obuff), ("i", "o"), strict=True):
            Cmd._buff_arg(opts, arg, io)
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
