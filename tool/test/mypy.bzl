"""
Print all runfiles available to find the mypy executable.
"""

def _mypy_check_impl(ctx):
    mypy = ctx.executable._mypy
    srcs = ctx.files.srcs
    deps = ctx.files.deps

    all_files = [f.path for f in srcs] + [f.path for f in deps]

    # Declare a validation output file (even if empty).
    validation_output = ctx.actions.declare_file(ctx.attr.name + "mypy.validation")

    # Run `mypy`, create a dummy output file for validation.
    ctx.actions.run_shell(
        inputs = srcs + deps,
        tools = [mypy],
        outputs = [validation_output],
        command = "{} {} && touch {}".format(mypy.path, " ".join(all_files), validation_output.path),
        progress_message = "Running mypy type checking.",
    )

    return [
        DefaultInfo(files = depset([])),  # No main outputs.
        OutputGroupInfo(_validation = depset([validation_output])),
    ]

mypy_check = rule(
    implementation = _mypy_check_impl,
    # test = True,
    attrs = {
        "srcs": attr.label_list(allow_files = [".py"]),
        "deps": attr.label_list(),
        "_mypy": attr.label(
            default = Label("//test:mypy"),
            executable = True,
            cfg = "exec",
        ),
    },
)
