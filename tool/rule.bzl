def _preprocess_impl(ctx):
    py_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"]
    if not py_toolchain or not py_toolchain.py3_runtime:
        fail("No Python toolchain resolved.")
    runtime = py_toolchain.py3_runtime
    interpreter = runtime.interpreter or runtime.interpreter_path

    srcs = ctx.files.srcs
    if len(srcs) == 0:
        fail("Sources `srcs` cannot be an empty list `[]`.")

    args = ctx.actions.args()
    args.add(ctx.attr._tool[DefaultInfo].files_to_run.executable)

    if ctx.attr.disable:
        args.add_all(("--stage", "none"))

    outs = []
    for src in srcs:
        stem, ext = src.basename.rsplit(".", 1)
        basename = stem + "." + (ctx.attr.out_ext or ext)
        out = ctx.actions.declare_file(src.dirname + "/" + basename)
        outs.append(out)

    args.add_all(as_opt_args("-o", outs))
    args.add_all(as_opt_args("-D", ctx.attr.local_defines))

    if not ctx.attr.keep_comments:
        args.add("--no-keep")

    args.add_all(srcs)

    ctx.actions.run(
        executable = interpreter,
        arguments = [args],
        inputs = ctx.files.srcs,
        tools = [ctx.attr._tool[DefaultInfo].files_to_run],
        outputs = outs,
        env = {
            "TOOL_LOG_LEVEL": "INFO",
            "TOOL_COLOR": "never",
            "TOOL_TRUNCATE": "never",
        },
        mnemonic = "PPTool",
        progress_message = "Processing `srcs` files with tool.",
    )
    return [DefaultInfo(files = depset(outs))]

def as_opt_args(opt, args):
    return [e for t in zip([opt] * len(args), args) for e in t]

cc_pp = rule(
    implementation = _preprocess_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [
                ".cppm",  # C++20 Importable module units.
                ".ccm",
                ".cxxm",
                ".c++m",
                ".cpp",  # C++20 Module implementation units.
                ".cc",
                ".cxx",
                ".c++",
                ".c",  # C files.
            ],
            mandatory = True,
            doc = """\
Source files to process.
[requirements][req] for the list of accepter extensions.
[req]: https://clang.llvm.org/docs/StandardCPlusPlusModules.html#file-name-requirements]
            """,
        ),
        "out_ext": attr.string(
            doc = """\
Extension to use for output files, e.g.
providing '.cpp' with 'main.cppm' in `srcrs`
will output 'main.cpp'.
            """,
        ),
        "local_defines": attr.string_list(
            doc = """\
Clang preprocessor defines, will be prepended with '-D', e.g.
providing 'COVERAGE' will append '-DCOVERAGE' to the list of
Clang options.
            """,
        ),
        "keep_comments": attr.bool(
            default = True,
            doc = """\
Whether to keep `#include`-s or remove them completely.
This works by excluding '-C' from the list of options supplied
to Clang. By default '-C' is included in this list.
            """,
        ),
        "disable": attr.bool(
            default = False,
            doc = """\
Disable preprocessing. Tool will still run but rewrite text
into output file as it appears in the source.
"""
        ),
        "_tool": attr.label(
            default = "//:tool",
            cfg = "target",
            doc = "The `py_binary` tool to run.",
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
)
