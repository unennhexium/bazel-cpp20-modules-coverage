def _preprocess_impl(ctx):
    outputs = []
    for src in ctx.files.srcs:
        base_list = src.basename.split(".")

        src_ext = base_list[-1]
        out_ext = ctx.attr.out_ext
        out_ext = out_ext if out_ext != "" else src_ext

        base_name = ".".join(base_list[:-1] + [out_ext])
        out = ctx.actions.declare_file("/".join([src.dirname, base_name]))

        tool = ctx.executable._tool

        # ctx.actions.run_shell(
        #     inputs = [src],
        #     outputs = [out],
        #     command = """
        #         set -eEuo pipefail

        #         echo >&2 '[DEBUG 1 (inputs)]'
        #         echo >&2 '{src}'
        #         echo >&2 '{out}'
        #         echo >&2 '{ext}'

        #         commented='{out}.commented.{ext}'
        #         if (({skip})); then
        #             skipped='{src}.skipped.{ext}'
        #             head -n {skip} > "$skipped"

        #             echo >&2 '[DEBUG 1 (skipped)]
        #             cat  >&2 "$skipped"

        #             tail -n +$(({skip} + 1)) {src}
        #         else
        #             cat '{src}'
        #         fi | sed -E "s=#include .*=// ___&=" > "$commented"

        #         echo >&2 '[DEBUG 2 (commented includes)]'
        #         cat  >&2 "$commented"

        #         uncommented='{out}.uncommented.{ext}'
        #         preprocessed='{out}.preprocessed.{ext}'
        #         clang -E -P {comments} -o "$preprocessed" "$commented"
        #         # clang -E -P -C -o "$uncommented" '{src}'

        #         echo >&2 '[DEBUG 3 (resolved pp derectives)]'
        #         cat  >&2 "$preprocessed"

        #         sed -E 's=// ___(#include .*)=\\1=' "$preprocessed" > "$uncommented"

        #         echo >&2 '[DEBUG 4 (uncommented includes)]'
        #         cat  >&2 "$uncommented"

        #         (({skip})); && mv -fv  "$skipped" '{out}'
        #         cat "$uncommented" >> '{out}'

        #         (({skip})) && {
        #             echo >&2 '[DEBUG 5 (merged with skipped)]'
        #             cat  >&2 "$uncommented"
        #         }
        #         false
        #     """.format(
        #         defs = " ".join(["-D" + str(d) for d in ctx.attr.local_defines]),
        #         out = out.path,
        #         src = src.path,
        #         ext = out_ext,
        #         comments = "-C " if ctx.attr.keep_comments else "",
        #         skip = ctx.attr.skip_lines,
        #     ),
        #     progress_message = "Preprocessing '%s' with `clang -E`." % src.short_path,
        # )
        ctx.actions.run(
            inputs = [src],
            outputs = [out],
            executable = tool,
            arguments = [src.path, out.path],
            progress_message = "Preprocessing %s with python tool." % src.short_path,
        )
        outputs.append(out)
    return [DefaultInfo(files = depset(outputs))]

preprocess = rule(
    implementation = _preprocess_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".cpp", ".cppm"], default = []),
        "local_defines": attr.string_list(default = []),
        "out_ext": attr.string(default = ""),
        "keep_comments": attr.bool(default = True),
        "skip_lines": attr.int(default = 0),
        "_tool": attr.label(
            default = "//:pp_tool",
            executable = True,
            cfg = "exec",
        ),
    },
)
