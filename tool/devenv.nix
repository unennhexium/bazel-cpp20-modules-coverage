{ pkgs, inputs, config, ... }:
with inputs;
let python = pkgs.python314FreeThreading;
in let
  # https://pyproject-nix.github.io/uv2nix/usage/getting-started.html
  # https://github.com/cachix/devenv/blob/1465d89d80e0f75ccd12176b882ba2634e87a1df/src/modules/languages/python/default.nix#L607-L642
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
in let
  overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
  pythonBase =
    pkgs.callPackage pyproject-nix.build.packages { inherit python; };
  pythonSet = pythonBase.overrideScope (pkgs.lib.composeManyExtensions [
    pyproject-build-systems.overlays.default
    overlay
  ]);
  # venv = config.languages.python.import ./. { };
  venv = pythonSet.mkVirtualEnv "tool-env" workspace.deps.default;
in let
  # https://pyproject-nix.github.io/uv2nix/patterns/applications.html
  inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
  tool = mkApplication {
    inherit venv;
    package = pythonSet.tool;
  };
in {
  env = {
    # UV_NO_SYNC = "1";
    UV_PYTHON = config.languages.python.package.interpreter;
    UV_PYTHON_DOWNLOADS = "never";
  };
  packages = [ tool ] ++ (with pkgs; [ asciinema_3 bazelisk ruff termsvg ]);
  languages.python = {
    enable = true;
    package = python;
    uv = {
      enable = true;
      sync = {
        enable = true;
        allGroups = true;
      };
    };
  };
  enterShell = ''
    [[ -d bazel-external ]] || ln -sf "$(bazel info execution_root)"/external bazel-external
    source "$DEVENV_STATE"/venv/bin/activate
  '';
  scripts.bazel.exec = ''bazelisk "$@"'';
  tasks."py:test".exec = "uv run -- pytest --verbosity=4 -rA";
  tasks."py:check".exec = "uv run -- mypy src/tool/__main__.py";
  outputs = { inherit tool; };
}
