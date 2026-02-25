import subprocess  # noqa: S404
import timeit
import tracemalloc
from functools import wraps
from typing import TYPE_CHECKING

from tool.lib.pretty import display_top
from tool.log.color import FIELD_MAP, Color
from tool.log.const import Field
from tool.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable


def time(*, colored: bool) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def _time(fun: Callable[[], None]):
        @wraps(fun)
        def wrap():
            start = timeit.default_timer()
            logger.warning("started time counting")
            fun()
            end = timeit.default_timer()
            logger.warning("stopped time counting")
            TIME, CR = (FIELD_MAP[Field.MSECS], Color.RESET)  # noqa: N806
            if not colored:
                TIME, CR = "", ""  # noqa: N806
            logger.warning(f"total time in processing:{TIME}%f{CR} sec", end - start)

        return wrap

    return _time


def trace(
    filters: list[str] | None,
    *,
    colored: bool,
) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def _trace(fun: Callable[[], None]):
        @wraps(fun)
        def wrap():
            tracemalloc.start()
            logger.warning("started tracing")
            # If there any unhandled exeption, `tracemaloc`
            # will block interpreter from exit, so wrap the
            # rest into `try`/`finally`.
            try:
                fun()
                snapshot = tracemalloc.take_snapshot()
            except Exception as e:  # noqa: BLE001
                logger.exception("exception accured: %s", e)
            else:
                fs = []
                if filters is not None:
                    if "self" in filters:
                        fs.append(tracemalloc.Filter(False, tracemalloc.__file__))  # noqa: FBT003
                    if "sub" in filters:
                        fs.append(tracemalloc.Filter(False, subprocess.__file__))  # noqa: FBT003
                display_top(snapshot, filters=fs, colored=colored)
            finally:
                logger.warning("stopping tracing")
                tracemalloc.stop()
                logger.warning("stopped tracing")

        return wrap

    return _trace
