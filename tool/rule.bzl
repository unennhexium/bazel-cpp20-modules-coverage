def _preprocess_impl(ctx):
    toolchain = ctx.toolchains["//toolchains:preprocess_toolchain_type"]
    py_tool = toolchain.preprocess.py_tool
    outputs = []
    for src in ctx.files.srcs:
        base_list = src.basename.split(".")

        src_ext = base_list[-1]
        out_ext = ctx.attr.out_ext
        out_ext = out_ext if out_ext != "" else src_ext

        base_name = ".".join(base_list[:-1] + [out_ext])
        out = ctx.actions.declare_file("/".join([src.dirname, base_name]))

        ctx.actions.run(
            inputs = [src],
            outputs = [out],
            executable = py_tool,
            arguments = [src.path, out.path],
            progress_message = "Preprocessing %s with python tool." % src.short_path,
        )
        outputs.append(out)
    return [DefaultInfo(files = depset(outputs))]

preprocess = rule(
    implementation = _preprocess_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".cpp", ".cppm"]),
        "local_defines": attr.string_list(),
        "out_ext": attr.string(),
        "keep_comments": attr.bool(default = True),
        "skip_lines": attr.int(default = 0),
        # "_tool": attr.label(
        #     default = "//:pp_tool",
        #     executable = True,
        #     cfg = "exec",
        # ),
    },
    toolchains = ["//tools:preprocess_toolchain_type"],
)
