from __future__ import annotations

import logging
from logging import LogRecord
from shutil import get_terminal_size
from typing import ClassVar, cast

from tool.arg.prep import Width
from tool.lib.util import is_list_wo_none
from tool.log.color import FIELD_MAP
from tool.log.const import Color, Field


class Formatter(logging.Formatter):
    LVL_FIELDS: ClassVar = {Field.LEVELNAME, Field.LEVELNO}

    def __init__(
        self,
        fields: list[Field],
        *,
        colored: bool = False,
        width: tuple[Width, int] = (Width.ALWAYS, 0),
    ):
        self.fields: dict[Field, str | None] = dict.fromkeys(fields, None)
        self.colored = colored
        match width:
            case Width.ALWAYS, _:
                self.cols = get_terminal_size((80, 20)).columns
            case Width.NEVER, _:
                self.cols = 0
            case Width.CUSTOM, cols:
                self.cols = cols
            case _:
                msg = "Non-exhaustive `match` statement."
                raise RuntimeError(msg)

    def format(self, record: LogRecord):
        record.funcName += "()"
        splitted = cast("list[str | None]", [None]) * len(self.fields) * 4
        acc = 0
        cols = self.cols
        keys: list[Field] = list(self.fields.keys())
        if cols < 0:
            keys.reverse()
        overflow = False
        for ind, fld in enumerate(keys):
            if fld == Field.MESSAGE:
                val = record.getMessage()
            else:
                val = record.__dict__[fld.value]
            str_val = str(val)
            acc += len(str_val) + 1
            if cols != 0 and acc >= abs(cols):
                str_val = str_val[: cols - acc] if cols > 0 else str_val[acc + cols :]
            left = str(FIELD_MAP[fld])
            right = str(Color.RESET)
            if cols < 0:
                left, right = right, left
            splitted[ind * 4 : (ind + 1) * 4] = [left, str_val, right, ":"]
            if cols != 0 and acc >= abs(cols):
                overflow = True
                break
        splitted = splitted[:-1]
        if cols < 0:
            splitted.reverse()
        assert is_list_wo_none(splitted)  # noqa: S101
        res = "".join(splitted)
        if cols != 0 and overflow:
            return res + "…" if cols > 0 else "…" + res
        return res
