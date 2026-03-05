from __future__ import annotations

import logging
from logging import LogRecord
from shutil import get_terminal_size
from typing import ClassVar, cast

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
        width: int = 0,
    ) -> None:
        self.fields: dict[Field, str | None] = dict.fromkeys(fields, None)
        self.colored = colored
        match width:
            case 0:
                self.cols = get_terminal_size((80, 20)).columns
            case -1:
                self.cols = 0
            case cols:
                self.cols = cols

    def format(self, record: LogRecord) -> str:
        record.funcName += "()"
        keys: list[Field] = list(self.fields.keys())
        match self.cols, self.colored:
            case 0, _:
                return Formatter._join(record, keys)
            case _, True:
                return self._join_and_cut(record, keys)
            case _, False:
                return Formatter._join(record, keys)[: self.cols]
            case _, _:
                msg = "None exhaustve `match` statement."
                raise RuntimeError(msg)

    def _join_and_cut(self, record: LogRecord, keys: list[Field]) -> str:
        splitted = cast("list[str | None]", [None]) * len(self.fields) * 4
        cols = self.cols
        if cols < 0:
            keys.reverse()
        acc = 0
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
        if overflow:
            return res + "…" if cols > 0 else "…" + res
        return res

    @staticmethod
    def _join(record: LogRecord, keys: list[Field]) -> str:
        return ":".join([
            record.getMessage()
            if fld == Field.MESSAGE
            else str(record.__dict__[fld.value])
            for fld in keys
        ])
