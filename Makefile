.PHONY: sym mod nomod cov check convert query

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
	cat modules/test.cpp | $(prog) -s pre -o - - | \
	tee >(print PRE) | $(prog) -s mid -o - - | \
	tee >(print MID) | $(prog) -s post -o - - | \
	print POST

# Display diff/diff3 between the results of the each stage.
diff:
	@pre=$$($(prog) -s pre -o - $$(realpath modules/test.cpp)) && \
	mid=$$(/usr/bin/clang -E -C -P -o - - -DCOVERAGE <<<$$pre) && \
	post=$$($(prog) -s post -o - - <<<$$mid) && \
	echo -e "[PRE]\n\n$$pre\n" && \
	echo -e "[MID]\n\n$$mid\n" && \
	echo -e "[POST]\n\n$$post\n"
#   | diff -y <(echo "$$pre") <(echo "$$post")
# 	| diff3 <(echo "$$pre") <(echo "$$mid") <(echo "$$pst")
# 	| grep -E --color=always '[[:digit:]]+[;#]|^'

# Run "pre" -> clang -> "post" pipe.
run_pipe:
	@LOG_LEVEL=DEBUG \
		$(prog) -s pre -o - $$(realpath modules/test.cpp) | \
		/usr/bin/clang -E -C -P -o - - | \
		$(prog) -s post -o - -

# Run all stages withing preprocessing script on three files concurently.
run_within:
	@LOG_LEVEL=DEBUG \
		$(prog) \
			-P always \
			-T never \
			-s pre mid post \
			-DCOVERAGE \
			modules/main.cpp -o - \
			modules/test.cpp -o - \
			modules/lib.cppm -o - \
			-t \
	2>&1 | grep -E --color=always 'Thread-[[:digit:]]|^'

number_of_files := 20

# Create a list of files to precess.
llvm:
	@echo total lines:
	@find llvm-project/llvm/lib/DebugInfo -type f -name '*.cpp' \
	| head -n $(number_of_files) | tee test_files.txt \
	| xargs cat | wc -l

# Run `ulimit -S -n 4096` in case of "OSError: [Errno 24] Too many open files".
run_llvm:
	@time LOG_LEVEL= $(prog) -tE @test_files.txt
