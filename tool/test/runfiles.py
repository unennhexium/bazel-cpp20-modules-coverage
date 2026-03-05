# ruff: noqa: T201, SLF001
from pathlib import PathRepr

from python.runfiles import Runfiles


def main():
    r = Runfiles.Create()

    if not r:
        print("No runfiles found")
        return

    print(f"Runfiles strategy: {type(r._strategy).__name__}")
    print(f"Current repository: {r.CurrentRepository()}")
    print()

    # For manifest-based runfiles, we can access the internal dictionary.
    if hasattr(r._strategy, "_runfiles"):
        print("All available runfiles:")
        for path, target in r._strategy._runfiles.items():
            if "mypy" in path.lower():
                print(f"  {path} -> {target}")
    else:
        # For directory-based runfiles, we can list the directory.
        runfiles_dir = PathRepr(r._strategy._runfiles_root)
        print(f"Runfiles directory: {runfiles_dir}")

        # Look for mypy-related files
        for root, _dirs, files in runfiles_dir.walk():
            for file in files:
                if "mypy" in file.lower():
                    rel_path = PathRepr(root, file).relative_to(runfiles_dir)
                    print(f"  {rel_path}")


if __name__ == "__main__":
    main()
