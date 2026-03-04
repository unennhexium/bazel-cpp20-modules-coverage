set quiet := true

mod tool

# Format Justfile-s and display available recipes.
[private]
fmt:
    just --fmt --unstable
    just --fmt --unstable --justfile tool/Justfile
    just --list --list-submodules --unsorted

# Symlink standard library module into "src" directory.
[group("bootstrap")]
sym:
    ln -vfs /usr/lib/llvm-*/share/libc++/v1 std

# Produce coverage data for package using C++20 modules.
[group("coverage")]
modules:
    just _cov --pack=modules --cov=1 # Changing to 0 should fail the build.

# Produce coverage data for package not using C++20 modules.
[group("coverage")]
nomodules:
    just _cov --pack=no_modules

# Produce coverage files.
[arg("pack", long="pack", short="p", help="- \tpackage for which to produce the coverage data")]
[arg("cov", long="cov", short="c", help="- \twhether to set 'cov' configuration parameter or not")]
[group("coverage")]
_cov $pack $cov="0":
    bazel coverage --config=coverage --define=cov="$cov" //"$pack":test

# Check the content of coverage output.
[group("coverage")]
check:
    head -n 3 bazel-out/_coverage/_coverage_report.dat
    grep -E '^(FN|FNDA|DA|BRDA|LH|LF)' bazel-out/_coverage/_coverage_report.dat | head -5
    find bazel-testlogs/_coverage -type f -exec cat '{}' ';'

# Generate HTML coverage report inside "genhtml" directory.
[group("coverage")]
convert:
    genhtml --output-directory genhtml bazel-out/_coverage/_coverage_report.dat && \
    open genhtml/index.html > /dev/null &

# FIXME: `--branch-coverage` - gives an error on "//modules:test" target coverage data.

# Perform query on coverage test target using C++20 modules.
[group("coverage")]
[arg("pack", long="pack", short="p", help="- \tpackage on which to run the quiery")]
query $pack="modules":
    bazel cquery --output=starlark \
    	--starlark:expr='providers(target)["InstrumentedFilesInfo"]' \
    	--config=coverage //"$pack":test

# Provide '-0' to inculde all files in the list

number_of_files := "20"

# Count the number of lines in all *.cpp files.
[group("llvm")]
llvm_count:
    echo total lines:
    find llvm-project/ -type f -name '*.cpp' \
    | head -n {{ number_of_files }} | parallel 'cat {}' \
    | wc -l

# There are 10'302'161 lines in total.

# Create a list of files to precess.
[group("llvm")]
llvm_list:
    echo total files:
    find "$PWD"/llvm-project/ -type f -name '*.cpp' \
    | head -n {{ number_of_files }} | tee test_files.txt \
    | wc -l

# There are 36'636 files in total. 281 line per-file on average.

# Run in test mode over the list of files.
[group("llvm")]
llvm_run:
    just tool::over_llvm @../test_files.txt

# Increase soft limit on the number of files oppened.
[group("llvm")]
set_soft_lim:
    ulimit -S -n 36636
