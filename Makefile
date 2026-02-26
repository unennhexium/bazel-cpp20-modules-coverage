.PHONY: sym mod nomod cov check convert query full diff run_* gen_llvm

SHELL := bash

pack := "modules"
cov := "1"

# Symlink standard library module into "src" directory.
sym:
	ln -vfs /usr/lib/llvm-*/share/libc++/v1 std

# Create coverage files for C++20 modules subproject.
mod:
	make cov pack=modules

# Create coverage files for subproject not using C++20 modules.
nomod:
	make cov pack=no_modules

# Produce coverage files.
cov:
	bazel coverage --config=coverage --define=cov=$(cov) //$(pack):test

# Produce coverage files.
uncov:
	make cov cov=0

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
	bazel cquery --output=starlark \
		--starlark:expr='providers(target)["InstrumentedFilesInfo"]' \
		--config=coverage //$(pack):test

# FIXME: `--branch-coverage` - gives an error on "//modules:test" target coverage data.

python := .venv/bin/python
prog := $(python) -O -- main.py

# Run each stage of the preprocessing script piped one into another.
full:
	@print() { read -rd '' txt; echo -e "[$$1]\n\n$$txt\n" >&2; }; \
	cat modules/test.cpp | $(prog) -s pre -- - | \
	tee >(print PRE) | $(prog) -s mid -- - | \
	tee >(print MID) | $(prog) -s post -- -| \
	print POST

# Display diff/diff3 between the results of the each stage.
diff:
	@pre=$$($(prog) -s pre -- $$(realpath modules/test.cpp)) && \
	mid=$$(/usr/bin/clang -E -C -P - -DCOVERAGE <<<$$pre) && \
	post=$$($(prog) -s post -- - <<<$$mid) && \
	echo -e "[PRE]\n\n$$pre\n" && \
	echo -e "[MID]\n\n$$mid\n" && \
	echo -e "[POST]\n\n$$post\n"
#   | diff -y <(echo "$$pre") <(echo "$$post")
# 	| diff3 <(echo "$$pre") <(echo "$$mid") <(echo "$$pst")
# 	| grep -E --color=always '[[:digit:]]+[;#]|^'

# Run "pre" -> clang -> "post" pipe.
run_pipe:
	@LOG_LEVEL=DEBUG \
		$(prog) -s pre -- $$(realpath modules/test.cpp) | \
		/usr/bin/clang -E -C -P - | \
		$(prog) -s post -- -

# Run all stages withing preprocessing script on three files concurently.
run_within:
	@LOG_LEVEL=DEBUG \
		$(prog) \
			-C always \
			-s pre mid post \
			-DCOVERAGE \
			modules/main.cpp \
			modules/test.cpp \
			modules/lib.cppm # \
# 	2>&1 | grep -E --color=always 'DEBUG'

# Provide '-0' to inculde all files in the list
number_of_files := 20

# Count the number of lines in all *.cpp files insice llvm-project repo.
count_llvm:
	@echo total lines:
	@find llvm-project/ -type f -name '*.cpp' \
	| head -n $(number_of_files) | parallel 'cat {}' \
	| wc -l

# There are 10'302'161 lines in total.

# Create a list of files to precess.
list_llvm:
	@ echo total files:
	@find llvm-project/ -type f -name '*.cpp' \
	| head -n $(number_of_files) | tee test_files.txt \
	| wc -l

# There are 36'636 files in total. 281 line per-file on average.

# Run in test mode over the list of files.
run_llvm:
	@time LOG_LEVEL= $(prog) -tTc \\-Wno-everything @test_files.txt

# Run `ulimit -S -n 36636` in case of "OSError: [Errno 24] Too many open files".
