from __future__ import annotations

import json

from tool.log.logger import logger


class Line:
    _id: int | None

    def __init__(
        self,
        line: str,
        pref: str,
        suff: str,
        delim: str | None = None,
    ) -> None:
        self.line = line
        self.pref, self.suff = pref, suff
        self.delim = delim if delim is not None else "\0"
        self._id = None

    def __str__(self) -> str:
        return self._repr(indent=True)

    def __repr__(self) -> str:
        return self._repr(indent=False)

    def _repr(self, *, indent: bool) -> str:
        return json.dumps(self.__dict__, indent=2 if indent else None)

    @property
    def id(self) -> int:
        if self._id is not None:
            return self._id
        if (
            len(self.line) == 0
            or not self.line.startswith(self.pref)
            or not self.line.endswith(self.suff)
        ):
            self._id = -1
            return self._id
        if __debug__:
            for k, v in self.__dict__.items():
                logger.debug("self.%s='%s'", k, v)
        logger.debug("(before strip):%s", f"{self.line=}")
        stripped = self.line[len(self.pref) : -len(self.suff)]
        logger.debug("(after strip, before slice): %s", f"{stripped=}")
        try:
            ind = stripped.index(self.delim)
            logger.debug("%s", f"{ind=}")
            mb_id = stripped[:ind]
            stripped = stripped[ind + 1:]
        except ValueError:
            logger.debug("no delim (%s) found", f"{self.delim=}")
            mb_id = stripped
            stripped = ""
        logger.debug("(after slice):%s", f"{mb_id=}")
        logger.debug("(after slice):%s", f"{stripped=}")
        self.line = stripped
        try:
            self._id = max(int(mb_id), -1)
        except ValueError:
            self._id = -1
        return self._id
