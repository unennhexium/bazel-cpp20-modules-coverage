{ pkgs, ... }: {
  packages = with pkgs; [
    bazelisk
    coreutils
    git
    jq
    just
    lcov
    llvmPackages_22.libcxxClang
    nil
    nixfmt
  ];
  scripts.bazel.exec = ''bazelisk "$@"'';
}
