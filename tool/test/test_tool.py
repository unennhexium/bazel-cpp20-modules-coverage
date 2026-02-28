# ruff: noqa: S101

import os
import re
import stat
import sys
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired  # noqa: S404
from typing import NamedTuple

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, *sys.argv[1:]]))

IS_BAZEL_TEST = (
    os.environ.get("BAZEL_PY_TEST", None) is not None
    and os.environ.get("TEST_ENVIRONMENT", "") == "bazel"
)

CWD = Path.cwd()

if IS_BAZEL_TEST:
    from python.runfiles import Runfiles

    RFS = Runfiles.Create()
elif not CWD.match("*/minimal/tool"):
    msg = "Current directory does not end with '/minimal/tool'."
    raise RuntimeError(msg)


class Tool(NamedTuple):
    prog: Path
    env: dict[str, str]


@pytest.fixture
def tool() -> Tool:
    if IS_BAZEL_TEST:
        info = sys.version_info
        name = f"tool_{info.major}_{info.minor}"
        path = RFS.Rlocation(Path("tool", name).as_posix())
        assert path is not None
        tool = Path(path)
        env = RFS.EnvVars()
        mode = 0o555
    else:
        tool = Path(CWD.joinpath("main.py"))
        # Inherit env from the parent process.
        # Actvate venv before running tests to
        # make dependences available.
        env = os.environ
        mode = 0o775
    assert tool.exists()
    assert tool.is_file()
    tool_mode = stat.S_IMODE(tool.stat().st_mode)
    assert tool_mode == mode, f"{tool_mode:0o}"
    env["LOG_LEVEL"] = "ERROR"
    return Tool(tool, env)


@pytest.fixture
def file() -> Path:
    if IS_BAZEL_TEST:
        path = RFS.Rlocation(CWD.joinpath("test", "data", "test.cpp").as_posix())
        assert path is not None
        file = Path(path)
    else:
        file = Path("test/data/test.cpp")
    assert file.exists()
    assert file.is_file()
    file_mode = stat.S_IMODE(file.stat().st_mode)
    assert file_mode == 0o0664, f"{file_mode:0o}"  # noqa: PLR2004
    return Path(file)


def test_pre(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s pre -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        pre, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    pattern = """\
int (\\d+);
/\\* (\\d+)#include <gtest/gtest\\.h> \\*/

#ifndef COVERAGE

import lib;

#else

int (\\d+);
/\\* (\\d+)#include "lib\\.cpp" \\*/

#endif

TEST\\(LibTest, HelloWorld\\) {
  EXPECT_EQ\\(greet\\(\\), "Hello, World!"\\);
}
"""
    err_str = f"\n\n[PAT]\n\n{pattern}\n\n[PRE]\n\n{pre}"
    matches = re.findall(pattern, pre)
    assert len(matches) == 1, err_str
    mch = matches[0]
    assert len(mch) == 4, err_str  # noqa: PLR2004
    assert mch[0] == mch[1], err_str
    assert mch[2] == mch[3], mch


def test_mid(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s mid -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        mid, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    lines = """\
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[MID]", mid]
    for e, r in zip(lines.split("\n"), mid.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))

    assert re.match(r"Subprocess '\d+' exited with non-zero code: 1", err)


def test_mid_define(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s mid -D COVERAGE=1 {file} -o -",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        mid, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    lines = """\
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[MID]", mid]
    for e, r in zip(lines.split("\n"), mid.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))
    assert re.match(r"Subprocess '\d+' exited with non-zero code: 1", err)


def test_post(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s post -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        post, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_pipe(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s pre -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        pre, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s post -o - {file}",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        post, err = proc.communicate(pre, timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[PRE]", pre, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_round_trip(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -s pre post -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        post, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0

    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} {file} -o -",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        full, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    lines = """\
#include <gtest/gtest.h>
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_define(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} -D COVERAGE -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        full, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    lines = """\
#include <gtest/gtest.h>
#include "lib.cpp"
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_no_keep(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} --no-keep -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        full, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    lines = """\
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_no_keep_define(tool: Tool, file: Path):
    proc = Popen(  # noqa: S602
        f"{tool.prog} --no-keep -D COVERAGE -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=tool.env,
    )
    try:
        full, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    lines = """\
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[IN]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))
