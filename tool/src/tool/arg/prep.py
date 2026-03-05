from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tool.arg.cmd import Cmd
from tool.arg.log import Color
from tool.arg.type import Log, Path, Select, Stage

if TYPE_CHECKING:
    from argparse import Namespace


class Arguments:
    def __init__(self, args: Namespace) -> None:
        self.raw = args
        self.stage = Stage(*args.stage)
        self.cmd = Cmd(args).build()
        self.path = Path(args.input, args.out)
        self.sels = Select(
            [re.compile(pat) for pat in args.pattern],
            [tuple(int(b) for b in rng.split(",")) for rng in args.range],
        )
        clr = args.color
        if isinstance(args.color, str):
            clr = Color.prepare(None, clr)
        self.log = Log(args.log, args.width, clr)
