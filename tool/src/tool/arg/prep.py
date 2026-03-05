from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tool.arg.cmd import Cmd
from tool.arg.type import Log, Path, Select, Stage

if TYPE_CHECKING:
    from argparse import Namespace


class Arguments:
    def __init__(self, args: Namespace) -> None:
        self.raw = args
        self.stages = Stage(*args.stage)
        self.cmd = Cmd(args).build()
        self.paths = Path(args.input, args.out)
        self.sels = Select(
            [re.compile(pat) for pat in args.pattern],
            [tuple(int(b) for b in rng.split(",")) for rng in args.range],
        )
        self.log = Log(args.log, args.width, args.color)
