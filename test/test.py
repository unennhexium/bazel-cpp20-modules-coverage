# ruff: noqa: S101

import re
import stat
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired  # noqa: S404

import pytest


@pytest.fixture
def file():
    assert Path.cwd().as_posix() == "/home/user/Desktop/minimal"
    file = Path("modules/test.cpp")
    assert file.exists()
    m_fi = stat.S_IMODE(file.stat().st_mode)
    assert m_fi == 0o0664, f"{m_fi:0o}"  # noqa: PLR2004
    return file


@pytest.fixture
def prog() -> Path:
    py = Path(".venv/bin/python")
    pr = f"LOG_LEVEL=ERROR {py} -- main.py"
    assert Path.cwd().as_posix() == "/home/user/Desktop/minimal"
    assert py.exists()
    m_py = stat.S_IMODE(py.stat().st_mode)
    assert m_py == 0o0775, f"{m_py:0o}"  # noqa: PLR2004
    return pr


def t_pre(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s pre -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_mid(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s mid -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_mid_define(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s mid -D COVERAGE=1 {file} -o -",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_post(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s post -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_pipe(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s pre -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    try:
        pre, err = proc.communicate(timeout=1.0)
    except TimeoutExpired:
        pytest.fail("Timeout expired.")
    assert len(err) == 0
    proc = Popen(  # noqa: S602
        f"{prog} -s post -o - {file}",
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_round_trip(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -s pre post -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_full(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} {file} -o -",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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


def t_full_define(file: Path, prog: Path):
    proc = Popen(  # noqa: S602
        f"{prog} -D COVERAGE -o - {file}",
        shell=True,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
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
