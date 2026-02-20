.PHONY: sym mod nomod check convert query

# Symlink standard library module into "src" directory.
sym:
	ln -s /usr/lib/llvm-*/share/libc++/v1 std

# Create coverage files for C++20 modules subproject.
mod:
	bazel coverage --config=coverage //modules:test

# Create coverage files for subproject not using C++20 modules.
nomod:
	bazel coverage --config=coverage //no_modules:test

# Check the content of coverage output directories and coverage file.
check:
	head -n 3 bazel-out/_coverage/_coverage_report.dat
	grep -E '^(FN|FNDA|DA|BRDA|LH|LF)' bazel-out/_coverage/_coverage_report.dat | head -5
	find bazel-testlogs/_coverage -type f -exec cat '{}' ';'

# Generate HTML coverage report inside "genhtml" directory.
convert:
	genhtml --output-directory genhtml bazel-out/_coverage/_coverage_report.dat && \
	open genhtml/index.html > /dev/null &

# Perform query on coverage test target using C++20 modules.
query:
	bazel cquery --output=starlark --starlark:file=query.py --config=coverage //modules:test

# FIXME: `--branch-coverage` - gives an error on "//modules:test" target coverage data.
