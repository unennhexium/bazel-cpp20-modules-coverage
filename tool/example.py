#!/usr/bin/env python3

import sys
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen  # noqa: S404


def main():
    cmd = ["/usr/bin/stdbuf", "-oL", "-eL", "/usr/bin/cat"]
    proc = Popen(  # noqa: S603
        cmd,
        stdin=PIPE,
        stdout=PIPE,
        stderr=DEVNULL,
        encoding="utf-8",
    )
    with (
        Path("modules/lib.cppm").open(encoding="utf-8") as src,
        Path("/dev/stdout").open("w", encoding="utf-8") as dst,
    ):
        # Write each line to the child and read the echoed line back.
        # Must flush after writing to ensure the child receives the data
        # and to avoid blocking on the read.
        for line in src:
            proc.stdin.write(line)
            proc.stdin.flush()
            dst.write(proc.stdout.readline())

        # Close stdin to signal EOF to the child, then drain any remaining
        # output from stdout before waiting for exit to avoid deadlocks.
        proc.stdin.close()
        for rem in proc.stdout:  # noqa: FURB122
            dst.write(rem)
        proc.stdout.close()
    ret = proc.wait()
    sys.exit(ret)


if __name__ == "__main__":
    main()
