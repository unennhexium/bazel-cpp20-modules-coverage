import linecache
from tracemalloc import Filter
from typing import TYPE_CHECKING

from tool.log.color import FIELD_MAP, Color
from tool.log.const import Field
from tool.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import Iterable


def display_top(
    snapshot,
    key_type="lineno",
    limit=10,
    filters: Iterable[Filter] | None = None,
    *,
    colored: bool = False,
):
    """
    Display the `limimt` lines allocating the most memory with a pretty
    output ignoring <frozen importlib._bootstrap> and <unknown> files.
    """
    NUM, FILE, LINE, SIZE, CR = (  # noqa: N806
        FIELD_MAP[Field.THREAD],
        FIELD_MAP[Field.FILENAME],
        FIELD_MAP[Field.LINENO],
        FIELD_MAP[Field.MSECS],
        Color.RESET,
    )
    if not colored:
        NUM, FILE, LINE, SIZE, CR = "", "", "", "", ""  # type: ignore[assignment] # noqa: N806
    filters = [
        Filter(False, "<frozen genericpath>"),  # noqa: FBT003
        Filter(False, "<frozen importlib._bootstrap>"),  # noqa: FBT003
        Filter(False, "<unknown>"),  # noqa: FBT003
        *(filters or []),
    ]
    snapshot = snapshot.filter_traces(filters)
    top_stats = snapshot.statistics(key_type)

    logger.warning("top %s lines", limit)
    total = 0
    for index, stat in enumerate(top_stats[:limit], 1):
        total += stat.size
        frame = stat.traceback[0]
        logger.warning(
            f"#{NUM}%s{CR}: {FILE}%s{CR}:{LINE}%s{CR}: {SIZE}%.1f{CR} KiB",
            index,
            frame.filename,
            frame.lineno,
            stat.size / 1024,
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if len(line) != 0:
            logger.warning("\t%s", line)
    other = top_stats[limit:]
    if len(other) != 0:
        size = sum(stat.size for stat in other)
        total += size
        logger.warning(
            f"{NUM}%s{CR} other: {SIZE}%.1f{CR} KiB",
            len(other),
            size / 1024,
        )
    logger.warning(f"total allocated size: {SIZE}%.1f{CR} KiB", total / 1024)
