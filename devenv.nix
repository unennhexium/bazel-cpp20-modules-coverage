{ pkgs, ... }: {
  packages = with pkgs; [
    coreutils
    git
    just
    bazelisk
    llvmPackages_22.libcxxClang
    lcov
    nil
    nixfmt
    jq
  ];
  scripts.bazel.exec = ''bazelisk "$@"'';
}
