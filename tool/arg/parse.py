from __future__ import annotations

import logging
import sys
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    BooleanOptionalAction,
    Namespace,
    RawDescriptionHelpFormatter,
)
from pathlib import Path

from tool.arg.range import RangeAction
from tool.log.const import Color


class Formatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter): ...


colored = sys.stdout.isatty()

CG = Color.GREEN | Color.BOLD | Color.DIM
CC = Color.CYAN | Color.BOLD | Color.DIM
CB = Color.BLUE | Color.BOLD
CY = Color.YELLOW
CM = Color.MAGENTA | Color.ITALIC | Color.DIM
CI = Color.ITALIC | Color.BOLD | Color.DIM
CR = Color.RESET

if not colored:
    CG, CC, CB, CY, CM, CI, CR = "", "", "", "", "", "", ""  # type: ignore[assignment]


def parse_arguments(log_levels: dict[str, int]) -> Namespace:
    parser = ArgumentParser(
        description=f"""
{CB}NAME{CR}
    Preprocess {CI}C{CR}/{CI}C++{CR} files ignoring {CM}#include-s{CR}.

{CB}SYNOPSIS{CR}
    {sys.argv[0]} [{CG}-o{CR} | {CC}--out{CR} [{CG}-q | {CC}--queue{CR}] [{CG}-p | {CC}--poll{CR}]
        [{CG}-s{CR} | {CC}--stage{CR}] [{CG}-r{CR} | {CC}--range{CR}] {CY}INPUT [{CY}INPUT{CR}...]
        [{CG}-p{CR} | {CC}--path{CR}] [{CG}-c{CR} | {CC}--clang{CR}] [{CG}-I | {CC}--ibuff{CR}] [{CG}-O{CR} | {CC}--obuff{CR}]
            [{CG}-D{CR} | {CC}--define{CR}] [{CG}-C{CR} | {CC}--keep{CR} | {CC}--no-keep{CR}]
        [{CG}-l{CR} | {CC}--log{CR}] [{CG}-R | {CC}--color{CR}] [{CG}-T{CR} | {CC}--truncate{CR}] [{CG}-W | {CC}--width{CR}]
    {sys.argv[0]} [{CG}-s{CR} | {CC}--script{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]
    {sys.argv[0]} [{CG}-t{CR} | {CC}--test{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]
    {sys.argv[0]} [{CG}-E{CR} | {CC}--time{CR}] [{CG}-M{CR} | {CC}--mem{CR}] [{CG}-F{CR} | {CC}--filter{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]


{CB}DESCRIPTION{CR}
    {CY}pre{CR} stage

    Guard all {CM}#include{CR} pragmas with marker of the form {CM}int ABC{CR}; and comment
    out those pragmas as {CM}/* ABC#include... */{CR}. {CM}ABC{CR} is some random integer.

    {CY}mid{CR} stage

    Process remaining derictives with clang preprocessor with {CG}-C{CR} specified
    by default (see {CG}-C{CR},{CC}--keep{CR} option) to retain comments and {CG}-P{CR}
    to not include a line markers at the beggining of the file.

    {CY}post{CR} stage

    Remove guarding markers and commented derictives which do not have a
    guard anymore since clang preprocessor has removed the range of lines,
    because of not satisfied {CM}#ifdef{CR}/{CM}#ifndef{CR} pragmas around the marker.
        """,  # noqa: E501
        formatter_class=Formatter,
        epilog=f"""
{CB}NOTES{CR}
    {CG}-E{CR},{CC}--time{CR} and {CG}-M{CR}{CC}--mem{CR} flags require at least {CY}WARNING{CR} (default) log level.
    The time and memory profiling result are printed as warning messages. This
    is expected when this flags are present.

    By default the first {CI}clang{CR} found in {CM}$PATH{CR} is used. Also see {CG}-p{CR},{CC}--path{CR} option.

    {CG}-I{CR},{CC}--ibuff{CR} and {CG}-O{CC},{CC}--outbuf{CR} options requre {CI}stdbuf{CC} executable to be in {CM}$PATH{CR}.

{CB}CAVEATS{CR}
    The script proces input files into output files in pairs. If the number
    of input and output files deffer, the script will stop when the shortest
    sequence is exhausted.

    The exception is no ouput specified; in this case the resulting lines are
    concatenaited into stdout. This is to assist testing a simple configurations.

    Each pair is processed concurently, so repeated output file arguments will
    cause the arbitrary ordering of lines inside such output file. The ordering
    is not deterministic, that is each run likely to produce the new permutation
    of output lines.
        """,  # noqa: E501
        fromfile_prefix_chars="@",
        prefix_chars="-+",
        # suggest_on_error=True,
        usage="%(prog)s [options]",
    )

    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.0.1")

    grp_io = parser.add_argument_group("input and output files")

    grp_io.add_argument(
        "input",
        default=["-"],
        help=(
            f"input file path(s), use {CY}-{CR} to read from stdin; "
            f"prepend with {CY}@{CR} to treat as file to read input "
            "file paths from (one per-line)"
        ),
        nargs="*",
        type=Path,
    )

    grp_io.add_argument(
        "-o",
        "--out",
        default=["-"],
        help=(
            f"output file path, use {CY}-{CR} to output to stdout; "
            f"prepend with {CY}@{CR} to treat as file to read output "
            "file paths from (one per-line)"
        ),
        metavar="OUT",
        nargs=1,
        type=Path,
    )

    grp_io.add_argument(
        "-q",
        "--queue",
        default=0,
        help=(
            f"line queue size limit for comminicating with {CI}clang{CR}; "
            "value <= 0 makes queue size unbound"
        ),
        metavar="SIZE",
        type=int,
    )

    grp_io.add_argument(
        "-P",
        "--poll",
        default=1.0,
        help="period [sec] for polling each io thread until it finished their work",
        metavar="TIME",
        type=float,
    )

    grp_io.add_argument(
        "-t",
        "--test",
        help=f"discard all output to {CM}/dev/null{CR}",
        action="store_true",
    )

    grp_stages = parser.add_argument_group("selecting stages")

    grp_stages.add_argument(
        "-s",
        "--stage",
        choices=["pre", "mid", "post", "full"],
        default=["full"],
        help="what stages to run",
        nargs="+",
    )

    grp_stages.add_argument(
        "-S",
        "--script",
        default="clang -E -P -C -o - -",
        help=f"run shell scrpt instead of the default {CI}clang{CR} command",
    )

    grp_sel = parser.add_argument_group("selecting lines")

    grp_sel.register("action", "build_range_action", RangeAction)

    grp_sel.add_argument(
        "-r",
        "--range",
        action="build_range_action",
        help="process only specified line range(s) (default: process entire file)",
        metavar="RANGE",
        nargs="+",
    )

    grp_clang = parser.add_argument_group("compiler settings")

    grp_clang.add_argument(
        "-p",
        "--path",
        help=f"path to {CI}clang{CR} compiler (default: search in {CM}$PATH{CR})",
        metavar="EXEC",
        nargs=1,
        type=Path,
    )

    grp_clang.add_argument(
        "-c",
        "--clang",
        action="extend",
        help=f"arguments forwarder to {CI}clang{CR}",
        metavar="ARG",
        nargs="+",
    )

    grp_clang.add_argument(
        "-I",
        "--ibuff",
        choices=["def", "line", "zero"],
        default="def",
        help=f"buffering for {CI}clang{CR} process stdin",
    )

    grp_clang.add_argument(
        "-O",
        "--obuff",
        choices=["def", "line", "zero"],
        default="def",
        help=f"buffering for {CI}clang{CR} process stdout",
    )

    grp_clang = parser.add_argument_group("preprocessor behavior")

    grp_clang.add_argument(
        "-D",
        "--define",
        action="extend",
        metavar="DEF",
        nargs="+",
    )

    grp_clang.add_argument(
        "-C",
        "--keep",
        action=BooleanOptionalAction,
        default=True,
        help=f"whether to add {CG}-C{CR} option to {CI}clang{CR} preprocessor",
    )

    grp_log = parser.add_argument_group("logging")

    grp_log.add_argument(
        "-l",
        "--log",
        choices=log_levels.keys(),
        default=logging.DEBUG,
        help="minimal log level to output",
        metavar="LEVEL",
        nargs="?",
        type=log_levels.get,  # -> int | None
    )

    grp_log.add_argument(
        "-R",
        "--color",
        default="auto",
        choices=["auto", "never", "always"],
        help="when color the logs",
        metavar="WHEN",
        nargs=1,
    )

    grp_log.add_argument(
        "-T",
        "--truncate",
        default="always",
        choices=["always", "never", "custom"],
        help=(
            f"when truncate the log line length (see also {CG}-W{CR},{CC}--width{CR})"
        ),
        metavar="WHEN",
    )

    grp_log.add_argument(
        "-W",
        "--width",
        help=(
            "force terminal value to this value "
            f"(see also {CG}-T{CR},{CC}--truncate{CR})"
        ),
        metavar="WIDTH",
        type=int,
    )

    grp_log.add_argument(
        "-E",
        "--time",
        help=f"measure the execution time using {CM}timeit{CR} module",
        action="store_true",
    )

    grp_log.add_argument(
        "-M",
        "--mem",
        help=(
            "print the memory footprint captured "
            f"using {CM}tracemalloc{CR} module using"
        ),
        action="store_true",
    )

    grp_log.add_argument(
        "-F",
        "--filter",
        choices=["self", "sub"],
        help=f"filter out {CM}tracemalloc{CR} results",
        nargs="+",
    )

    return parser.parse_intermixed_args()
