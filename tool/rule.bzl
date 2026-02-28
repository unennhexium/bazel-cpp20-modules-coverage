def _preprocess_impl(ctx):
    py_toolchain = ctx.toolchains["@rules_python//python:toolchain_type"]
    if not py_toolchain or not py_toolchain.py3_runtime:
        fail("No Python toolchain resolved.")
    runtime = py_toolchain.py3_runtime
    interpreter = runtime.interpreter or runtime.interpreter_path

    srcs = ctx.files.srcs
    outs = []
    for src in srcs:
        stem, ext = src.basename.rsplit(".", 1)
        basename = stem + "." + (ctx.attr.out_ext or ext)
        out = ctx.actions.declare_file(src.dirname + "/" + basename)
        outs.append(out)
    out_args = [e for t in zip(["-o"] * len(outs), outs) for e in t]

    args = ctx.actions.args()
    args.add(ctx.attr._tool[DefaultInfo].files_to_run.executable)
    args.add_all(ctx.files.srcs)
    args.add_all(out_args)

    ctx.actions.run(
        executable = interpreter,
        arguments = [args],
        inputs = ctx.files.srcs,  # + [ctx.attr._tool[DefaultInfo].files_to_run.executable],
        tools = [ctx.attr._tool[DefaultInfo].files_to_run],
        outputs = outs,
        env = {
            "LOG_LEVEL": "INFO",
        },
        mnemonic = "PPTool",
        progress_message = "Processing `srcs` files with tool.",
    )
    return [DefaultInfo(files = depset(outs))]

cc_pp = rule(
    implementation = _preprocess_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [
                ".cppm",
                ".ccm",
                ".cxxm",
                ".c++m",  # C++20 Importable module units.
                ".cpp",
                ".cc",
                ".cxx",
                ".c++",  # C++20 Module implementation units.
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
Extension to use for ouput files, e.g.
providing '.cpp' with 'main.cppm' in `srcrs`
will output 'main.cpp'.
            """,
        ),
        "local_defines": attr.string_list(
            doc = """\
Clang preprocessor defines, will be prepended with '-D', e.g.
providing 'COVERAGE' vill append '-DCOVERAGE' to the list of
Clang options.
            """,
        ),
        "keep_comments": attr.bool(
            default = True,
            doc = """\
Whether to keep `#include`-s or remove them completelly.
This works by excluding '-C' from the list of options supplied
to Clang. By default '-C' is included in this list.
            """,
        ),
        "_tool": attr.label(
            default = "//:tool",
            cfg = "target",
            doc = "The `py_binary` tool to run.",
        ),
    },
    toolchains = ["@rules_python//python:toolchain_type"],
)
