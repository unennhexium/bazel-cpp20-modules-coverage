from __future__ import annotations

import sys
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    BooleanOptionalAction,
    Namespace,
    RawDescriptionHelpFormatter,
)
from pathlib import Path

from tool.arg.log import Color as ColorAction
from tool.arg.log import level
from tool.arg.path import PathIn, PathOut
from tool.arg.stage import Stage
from tool.arg.type import PathRepr
from tool.log.const import Color
from tool.stage.mid import mid
from tool.stage.post import post
from tool.stage.pre import pre


class Formatter(RawDescriptionHelpFormatter, ArgumentDefaultsHelpFormatter): ...


colored = sys.stdout.isatty()

CG = Color.GREEN | Color.BOLD | Color.DIM
CC = Color.CYAN | Color.BOLD | Color.DIM
CB = Color.BLUE | Color.BOLD
CY = Color.YELLOW
CM = Color.MAGENTA | Color.ITALIC | Color.DIM
CI = Color.ITALIC | Color.BOLD | Color.DIM
CU = Color.UNDER_LINE | Color.BOLD
CR = Color.RESET

if not colored:
    CG, CC, CB, CY, CM, CI, CU, CR = "", "", "", "", "", "", "", ""  # type: ignore[assignment]


def parse_arguments(log_levels: dict[str, int]) -> Namespace:
    parser = ArgumentParser(
        description=f"""
{CB}NAME{CR}
    Preprocess {CI}C{CR}/{CI}C++{CR} files ignoring {CM}#include{CR}s.

{CB}SYNOPSIS{CR}
    {sys.argv[0]} [{CG}-o{CR} | {CC}--out{CR}] [{CG}-q{CR} | {CC}--queue{CR}] [{CG}-p{CR} | {CC}--poll{CR}]
        [{CG}-s{CR} | {CC}--stage{CR}] [{CG}-r{CR} | {CC}--range{CR}] {CY}INPUT [{CY}INPUT{CR}...]
        [{CG}-p{CR} | {CC}--path{CR}] [{CG}-c{CR} | {CC}--clang{CR}] [{CG}-I{CR} | {CC}--ibuff{CR}] [{CG}-O{CR} | {CC}--obuff{CR}]
            [{CG}-D{CR} | {CC}--define{CR}] [{CG}-K{CR} | {CC}--keep{CR} | {CC}--no-keep{CR}]
            [{CG}-P{CR} | {CC}--poll{CR}] [{CG}-U{CR} | {CC}--timeout{CR}]
        [{CG}-l{CR} | {CC}--log{CR}] [{CG}-C{CR} | {CC}--color{CR}] [{CG}-E{CR} | {CC}--truncate{CR}] [{CG}-W{CR} | {CC}--width{CR}]
    {sys.argv[0]} [{CG}-s{CR} | {CC}--script{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]
    {sys.argv[0]} [{CG}-t{CR} | {CC}--test{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]
    {sys.argv[0]} [{CG}-T{CR} | {CC}--time{CR}] [{CG}-M{CR} | {CC}--mem{CR}] [{CG}-F{CR} | {CC}--filter{CR}] {CY}INPUT{CR} [{CY}INPUT{CR}...]


{CB}DESCRIPTION{CR}
    {CY}pre{CR} stage

    Guard all {CM}#include{CR} pragmas with marker of the form {CM}int ABC{CR}; and comment
    out those pragmas as {CM}/* ABC#include... */{CR}. {CM}ABC{CR} is some random integer.

    {CY}mid{CR} stage

    Process remaining directives with clang preprocessor with {CG}-C{CR} specified
    by default (see {CG}-K{CR},{CC}--keep{CR} option) to retain comments and {CG}-P{CR}
    to not include a line markers at the beginning of the file.

    {CY}post{CR} stage

    Remove guarding markers and commented directives which do not have a
    guard anymore since clang preprocessor has removed the range of lines,
    because of not satisfied {CM}#ifdef{CR}/{CM}#ifndef{CR} pragmas around the marker.
        """,  # noqa: E501
        formatter_class=Formatter,
        epilog=f"""
{CB}ENVIRONMENT{CR}
    {CU}TOOL_LOG_LEVEL{CR} setting this takes precedence over {CG}-l{CR},{CC}--log{CR} option; see
    option description for the list of possible values; set but empty equals
    setting 'DEBUG'.

    {CU}TOOL_COLOR{CR} setting this takes precedence over {CG}-c{CR},{CC}--color{CR} option; see
    option description for the list of possible values; set but empt equals
    setting 'never'. Note that setting this or option does not affect the
    colorization of the help text. It is fixed to 'auto'.

    {CU}TOOL_TRUNCATE{CR} setting this takes precedence over {CG}-E{CR},{CC}--truncate{CR} option; see
    option description for the list of possible values; set but empty equals
    setting 'never'.

{CB}NOTES{CR}
    The default {CI}clang{CR} command is {CM}clang -E -P -C -o - -{CR}. See also {CG}-I{CR}, {CG}-O{CR}, {CG}-D{CR} and
    {CG}-S{CR} options' description.

    {CG}-E{CR},{CC}--time{CR} and {CG}-M{CR}{CC}--mem{CR} flags require at least {CY}WARNING{CR} (default) log level.
    The time and memory profiling result are printed as warning messages. This
    is expected when this flags are present.

    By default the first {CI}clang{CR} found in {CM}$PATH{CR} is used. Also see {CG}-p{CR},{CC}--path{CR}
    option.

    {CG}-I{CR},{CC}--ibuff{CR} and {CG}-O{CC},{CC}--outbuf{CR} options require {CI}stdbuf{CR} executable to be in {CM}$PATH{CR}.

    Providing negative argument to {CG}-W{CR},{CC}--width{CR} other than -1 results in left truncation
    on that width's absolute value.

    There is {CG}-i{CR} instead of {CG}-o{CR} option since {CI}argparse{CR} module evaluates
    positional arguments last, while the number of inputs should be known at the time of
    preparing outputs by design.

{CB}CAVEATS{CR}
    The script processes input files into output files in pairs. If the number
    of input and output files deffer, the script will stop when the shortest
    sequence is exhausted.

    The exception is no output specified; in this case the resulting lines
    are concatenated into stdout. This is to assist testing a simple
    configurations. See {CG}-t{CR} flag.

    Each pair is processed concurrently, so repeated output file arguments will
    cause the arbitrary ordering of lines inside those output file. The ordering
    is not deterministic, that is each run likely to produce the new permutation
    of output lines.

    The exception is stdin input specified multiple times; in this case repeated
    output file arguments paired with stdin are processed sequentially but still
    in arbitrary order; since input (stdin) is the same for each pair, the same
    should be the output, so the first available result is reused. That is,
    output consist of repeated fragments, the order of which cannot be noticed.
        """,  # noqa: E501
        fromfile_prefix_chars="@",
        prefix_chars="-+",
        # suggest_on_error=True,
        usage="%(prog)s [options]",
    )

    version = ["%(prog)s\t: \t0.0.1"]
    version.extend((f"python\t: \t{sys.executable}", f"version\t: \t{sys.version}"))

    parser.add_argument("-v", "--version", action="version", version="\n".join(version))

    grp_io = parser.add_argument_group("input and output files")

    grp_io.add_argument(
        "-i",
        "--input",
        action=PathIn,
        default=[PathRepr("/dev/stdin")],
        help=(
            f"input file path(s), use {CY}-{CR} to read from stdin; "
            f"prepend with {CY}@{CR} to treat as file to read input "
            "file paths from (one per-line)"
        ),
        metavar="IN",
        nargs="+",
    )

    grp_io.add_argument(
        "out",
        action=PathOut,
        default=[PathRepr("/dev/stdout")],
        help=(
            f"output file path, use {CY}-{CR} to output to stdout; "
            f"prepend with {CY}@{CR} to treat as file to read output "
            "file paths from (one per-line)"
        ),
        metavar="OUT",
        nargs="*",
    )

    grp_io.add_argument(
        "-q",
        "--queue",
        default=0,
        help=(
            f"line queue size limit for communicating with {CI}clang{CR}; "
            "value <= 0 makes queue size unbound"
        ),
        metavar="SIZE",
        type=int,
    )

    grp_io.add_argument(
        "-P",
        "--poll",
        default=1.0,
        help="period for polling each io thread until it finished their work",
        metavar="SEC",
        type=float,
    )

    grp_io.add_argument(
        "-U",
        "--timeout",
        default=1.0,
        help=f"time to wait until {CI}clang{CR} finished their work",
        metavar="SEC",
        type=float,
    )

    grp_stage = parser.add_argument_group("selecting stages")

    grp_stage.add_argument(
        "-s",
        "--stage",
        action=Stage,
        choices=["pre", "mid", "post", "all", "none"],
        default=[pre, mid, post],
        help=(
            "what stages to run; "
            f"{CY}all{CR} overrides separate stages; "
            f"{CY}none{CR} overrides {CY}all{CR}"
        ),
        nargs="+",
    )

    grp_stage.add_argument(
        "-S",
        "--script",
        help=(
            "run shell script instead of the default "
            f"{CI}clang{CR} command (see {CB}NOTES{CR})"
        ),
    )

    grp_sel = parser.add_argument_group("selecting lines")

    grp_sel.add_argument(
        "-a",
        "--pattern",
        default=[r"#[ \t]*include[ \t]+.*"],
        help=(
            "patterns to consider line a pragma to guard "
            f"(default: guard {CM}#include{CR}-s)"
        ),
        metavar="PAT",
        nargs="+",
    )

    grp_sel.add_argument(
        "-r",
        "--range",
        default=["0,-1"],
        help=(
            "process only specified line range(s); "
            '-1 at upper bound means "to the end of file"'
            "(default: process entire file) "
        ),
        metavar="RANGE",
        nargs="+",
    )

    grp_clang = parser.add_argument_group("compiler settings")

    grp_clang.add_argument(
        "-p",
        "--path",
        help=f"path to {CI}clang{CR} compiler (default: search in {CM}$PATH{CR})",
        metavar="EXEC",
        type=Path,
    )

    grp_clang.add_argument(
        "-c",
        "--clang",
        action="append",
        help=f"argument forwarder to {CI}clang{CR}",
        metavar="ARG",
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
        action="append",
        help=(
            f"{CI}clang{CR} preprocessor definitions "
            f"(used for resolving {CM}#ifdef{CR}/{CM}#ifndef{CR})"
        ),
        metavar="DEF",
    )

    grp_clang.add_argument(
        "-K",
        "--keep",
        action=BooleanOptionalAction,
        default=True,
        help=(
            f"whether to add {CG}-C{CR} option to {CI}clang{CR} preprocessor; "
            f"passing {CC}--no-keep{CR} will result in all {CM}#include{CR}s deleted"
        ),
    )

    grp_log = parser.add_argument_group("logging")

    grp_log.add_argument(
        "-l",
        "--log",
        action=level(log_levels),
        choices=log_levels.keys(),
        default=log_levels["WARNING"],
        help="minimal log level to output",
        metavar="LEVEL",
        type=log_levels.get,  # -> int | None
    )

    grp_log.add_argument(
        "-W",
        "--width",
        default=0,
        help=(
            "assume terminal has provided width; "
            f"{CY}0{CR} will get width from terminal, "
            f"while {CY}-1{CR} will disable truncation "
        ),
        metavar="WIDTH",
        type=int,
    )

    grp_log.add_argument(
        "-C",
        "--color",
        action=ColorAction,
        choices=["auto", "never", "always"],
        default="auto",
        help="when color the logs",
        metavar="WHEN",
    )

    grp_perf = parser.add_argument_group()

    grp_perf.add_argument(
        "-t",
        "--test",
        action="store_true",
        help=f"discard all output to {CM}/dev/null{CR}",
    )

    grp_perf.add_argument(
        "-T",
        "--time",
        action="store_true",
        help=f"measure the execution time using {CM}timeit{CR} module",
    )

    grp_perf.add_argument(
        "-M",
        "--mem",
        action="store_true",
        help=(
            "print the memory footprint captured "
            f"using {CM}tracemalloc{CR} module using"
        ),
    )

    grp_perf.add_argument(
        "-F",
        "--filter",
        choices=["self", "sub"],
        help=f"filter out {CM}tracemalloc{CR} results",
        nargs="+",
    )

    return parser.parse_intermixed_args()
