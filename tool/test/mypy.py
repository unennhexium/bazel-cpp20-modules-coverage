import subprocess  # noqa: S404
import sys

from python.runfiles import Runfiles


def main():
    # Create runfiles object to resolve dependencies
    r = Runfiles.Create()

    # Set up environment for subprocess
    env = dict(r.EnvVars())

    # Run mypy through the runfiles system
    # repo = "rules_python++pip+pypi_3_14_314_mypy"
    # target = (
    #     "mypy-1.19.1-cp314-cp314-manylinux2014_x86_64."
    #     "manylinux_2_17_x86_64.manylinux_2_28_x86_64."
    #     "whl"
    # )
    # entry = "rules_python_wheel_entry_point_mypy.py"
    # mypy_path = r.Rlocation(f"tool/external/{repo}/{entry}")

    path = "rules_python++pip+pypi_3_14_314_mypy/site-packages/mypy/main.py"
    # path = "rules_python++pip+pypi_3_14_314_mypy/site-packages/mypy/__main__.py"
    # path = "rules_python++pip+pypi_3_14_314_mypy/site-packages/mypy/__init__.py"

    mypy_path = r.Rlocation(path)

    python = sys.executable

    cmd = [python, mypy_path, *sys.argv[1:]]
    result = subprocess.run(cmd, env=env, check=False)  # noqa: S603
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
