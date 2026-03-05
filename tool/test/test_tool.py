# ruff: noqa: S101

import os
import re
import stat
import sys
from pathlib import Path
from typing import NamedTuple
from unittest.mock import Mock, mock_open, patch

import pytest

from tool import main

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
elif (DEVENV_STATE := os.environ.get("DEVENV_STATE", None)) is not None:
    pass
else:
    msg = "Run `bazel test` or `devenv tasks run pytest`."
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
        tool = Path(DEVENV_STATE, "venv", "bin", "tool")
        env = os.environ.copy()
        mode = 0o775
    assert tool.exists()
    assert tool.is_file()
    tool_mode = stat.S_IMODE(tool.stat().st_mode)
    assert tool_mode == mode, f"{tool_mode:0o}"
    env["TOOL_LOG_LEVEL"] = "ERROR"
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
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        if self.as_posix() == "/dev/stdout":
            return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch("sys.argv", ["-", "-s", "pre", "-i", file.as_posix()]),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
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
    pre = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    err_str = f"\n\n[PAT]\n\n{pattern}\n\n[PRE]\n\n{pre}"
    matches = re.findall(pattern, pre)
    assert len(matches) == 1, err_str
    mch = matches[0]
    assert len(mch) == 4, err_str  # noqa: PLR2004
    assert mch[0] == mch[1], err_str
    assert mch[2] == mch[3], mch


def test_mid(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()
    m_exit = Mock()

    def open_(self: Path, *args, **kwargs):
        if self.as_posix() == "/dev/stdout":
            return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch("sys.argv", ["-", "-s", "mid", "-i", file.as_posix()]),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
        patch("sys.exit", m_exit),
    ):
        main()
    lines = """\
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    mid = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    err = "".join(c.args[0] for c in m_exit.call_args_list)
    err_str = ["[EXP]", lines, "[MID]", mid]
    for e, r in zip(lines.split("\n"), mid.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))

    assert re.match(r"Subprocess '\d+' exited with non-zero code: 1", err)


def test_mid_define(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()
    m_exit = Mock()

    def open_(self: Path, *args, **kwargs):
        if self.as_posix() == "/dev/stdout":
            return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-s", "mid", "-D", "COVERAGE=1", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
        patch("sys.exit", m_exit),
    ):
        main()
    lines = """\
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    mid = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    err = "".join(c.args[0] for c in m_exit.call_args_list)
    err_str = ["[EXP]", lines, "[MID]", mid]
    for e, r in zip(lines.split("\n"), mid.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))
    assert re.match(r"Subprocess '\d+' exited with non-zero code: 1", err)


def test_post(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        if self.as_posix() == "/dev/stdout":
            return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-s", "post", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    post = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_pipe(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()
    m_stdin = None

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
            case "/dev/stdin":
                assert m_stdin is not None
                return m_stdin()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-s", "pre", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    pre = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)

    m_stdout.reset_mock()
    m_stdin = mock_open(read_data=pre)

    with (
        patch(
            "sys.argv",
            ["-", "-s", "post", "-i", "-"],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    post = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[PRE]", pre, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_round_trip(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-s", "pre", "post", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    post = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)

    with file.open("r", encoding="utf-8") as f:
        lines = "".join(f.readlines())
        err_str = ["[IN]", lines, "[POST]", post]
        for e, r in zip(lines.split("\n"), post.split("\n"), strict=False):
            assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    lines = """\
#include <gtest/gtest.h>
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_define(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-D", "COVERAGE", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    lines = """\
#include <gtest/gtest.h>
#include "lib.cpp"
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_no_keep(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "--no-keep", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    lines = """\
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_full_no_keep_define(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "--no-keep", "-D", "COVERAGE", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    lines = """\
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_stdin_cache(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
            case "/dev/stdin":
                return file.open(*args, **kwargs)
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-i", "-", "-", "--", "-"],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    full += m_stdout.return_value.writelines.call_args_list[0].args[0]
    lines = """\
#include <gtest/gtest.h>
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
#include <gtest/gtest.h>
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full, "[CALLS]", str(m_stdout.mock_calls)]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))


def test_rng(tool: Tool, file: Path):
    orig = Path.open
    m_stdout = mock_open()

    def open_(self: Path, *args, **kwargs):
        match self.as_posix():
            case "/dev/stdout":
                return m_stdout()
        return orig(self, *args, **kwargs)

    with (
        patch(
            "sys.argv",
            ["-", "-r", "1,-1", "-i", file.as_posix()],
        ),
        patch("os.environ", tool.env),
        patch("pathlib.Path.open", open_),
    ):
        main()
    full = "".join(c.args[0] for c in m_stdout.return_value.write.call_args_list)
    lines = """\
import lib;
TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
"""
    err_str = ["[EXP]", lines, "[POST]", full]
    for e, r in zip(lines.split("\n"), full.split("\n"), strict=False):
        assert e == r, "\n" + "\n\n".join((f"{e=}\n{r=}", *err_str))
