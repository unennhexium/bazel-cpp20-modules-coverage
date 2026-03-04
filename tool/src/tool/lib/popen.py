from __future__ import annotations

import sys
from contextlib import ContextDecorator
from queue import Queue
from subprocess import PIPE, Popen  # noqa: S404
from threading import Thread
from typing import TYPE_CHECKING, NewType

from tool.lib.util import plural
from tool.log.logger import logger

if TYPE_CHECKING:
    from types import TracebackType

type IOQueue = Queue[str | Sentinel]
Sentinel = NewType("Sentinel", StopIteration)


class PopenContext(ContextDecorator):
    EOF = Sentinel(StopIteration())  # Sentinel.

    def __init__(
        self,
        cmd: list[str],
        *,
        shell: bool = False,
        size: int = 0,
        poll: float = 1.0,
        timeout: float = 1.0,
    ) -> None:
        logger.debug("%s", f"{cmd=}")
        proc = Popen(  # noqa: S603
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            encoding="utf-8",
            shell=shell,
        )
        for fd, no in zip(
            (proc.stdin, proc.stdout, proc.stderr),
            range(3),
            strict=False,
        ):
            if fd is None:
                msg = f"fd #{no} is closed."
                raise OSError(msg)
        self.proc = proc
        self.size = size
        self.poll = poll
        self.timeout = timeout

    def __enter__(self) -> tuple[IOQueue, IOQueue, IOQueue]:
        self.q_in: IOQueue = Queue(self.size)
        self.q_out: IOQueue = Queue(self.size)
        self.q_err: IOQueue = Queue(self.size)
        self.th_in = Thread(target=self._writer)
        self.th_out = Thread(target=self._reader)
        self.th_err = Thread(target=self._reporter)
        logger.debug("trying to start child threads")
        self.th_in.start()
        self.th_out.start()
        self.th_err.start()
        return self.q_in, self.q_out, self.q_err

    def __exit__(
        self,
        Ty: type[BaseException] | None,  # noqa: N803
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            raise exc
        for th, qu in (
            (self.th_in, self.q_in),
            (self.th_out, self.q_out),
            (self.th_err, self.q_err),
        ):
            cnt = 0
            while True:
                th.join(timeout=self.poll)
                if th.is_alive():
                    logger.warning(
                        (
                            "thread '%s' has not yet finished:"
                            "checked %d time%s:"
                            "approximate number or remaining lines:%d"
                        ),
                        th.name,
                        cnt + 1,
                        plural(cnt),
                        qu.qsize(),
                    )
                    cnt += 1
                else:
                    break
            logger.debug(
                "thread '%s' has successfully terminated",
                th.name,
            )
        code = self.proc.wait(self.timeout)
        if code != 0:
            msg = f"Subprocess '{self.proc.pid}' exited with non-zero code: {code}"
            sys.exit(msg)

    def _writer(self) -> None:
        assert self.proc.stdin is not None  # noqa: S101
        for line in iter(self.q_in.get, PopenContext.EOF):
            assert isinstance(line, str)  # noqa: S101
            logger.debug("(stdin):%s", line.rstrip())
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
            self.q_in.task_done()
        self.q_in.task_done()
        self.proc.stdin.close()
        logger.debug("stdin has closed")

    def _reader(self) -> None:
        assert self.proc.stdout is not None  # noqa: S101
        for line in self.proc.stdout:
            logger.debug("(stdout):%s", line.rstrip())
            self.q_out.put(line)
        self.proc.stdout.close()
        self.q_out.put(PopenContext.EOF)
        logger.debug("stdout has closed")

    def _reporter(self) -> None:
        assert self.proc.stderr is not None  # noqa: S101
        for line in self.proc.stderr:
            logger.warning("(stderr):%s", line.rstrip())
            self.q_err.put(line)
        self.proc.stderr.close()
        self.q_err.put(PopenContext.EOF)
        logger.debug("stderr has closed")
