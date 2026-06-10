pkgs: pfinal: pprev:
let
  inherit (pkgs) lib;
in
pprev.nixpkgs-updaters-library.overridePythonAttrs (old: {
  version = "3.1.1.dev"; # @version
  src = ./..;

  postPatch = with pkgs; ''
    substituteInPlace nupd/executables.py \
      --replace-fail '"nurl"' '"${lib.getExe nurl}"' \
      --replace-fail '"nix-prefetch-url"' '"${lib.getExe' nix "nix-prefetch-git"}"' \
      --replace-fail '"nix-prefetch-git"' '"${lib.getExe' nix-prefetch-git "nix-prefetch-git"}"' \
      --replace-fail '"git"' '"${lib.getExe git}"'
  '';

  preCheck = (old.preCheck or "") + ''
    export HOME=$(mktemp -d)
    export PYTHONPATH=".:$PYTHONPATH"
    rm -rf docs/
  '';
  nativeCheckInputs = (lib.lists.remove pfinal.pytest-cov-stub old.nativeCheckInputs) ++ [
    (pfinal.callPackage ./lint-hook/lint-hook.nix { })
    pfinal.pytest-cov
  ];

  dependencies = with pfinal; [
    aiohttp
    cyclopts
    frozendict
    inject
    joblib
    loguru
    platformdirs
    pydantic
    rich
  ];
})
