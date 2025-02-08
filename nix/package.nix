{
  lib,
  buildPythonPackage,
  pythonOlder,

  # build-system
  hatchling,

  # dependencies
  aiohttp,
  attrs,
  frozendict,
  inject,
  loguru,
  nbdb,
  nix,
  nix-prefetch-git,
  nurl,
  platformdirs,
  typer,

  # tests
  lint-hook,
  pytestCheckHook,
  aioresponses,
  pytest-asyncio,
  pytest-cov,
  pytest-mock,
}:
buildPythonPackage {
  pname = "nixpkgs-updaters-library";
  version = "1.0.1.dev"; # @version
  pyproject = true;

  disabled = pythonOlder "3.12";

  src = ./..;

  postPatch = ''
    substituteInPlace nupd/executables.py \
      --replace-fail '"nurl"' '"${lib.getExe nurl}"' \
      --replace-fail '"nix-prefetch-url"' '"${nix}/bin/nix-prefetch-url"' \
      --replace-fail '"nix-prefetch-git"' '"${nix-prefetch-git}/bin/nix-prefetch-git"'
  '';

  build-system = [ hatchling ];

  dependencies = [
    aiohttp
    attrs
    frozendict
    inject
    loguru
    nbdb
    platformdirs
    typer
  ];

  nativeCheckInputs = [
    lint-hook
    pytestCheckHook

    aioresponses
    pytest-asyncio
    pytest-cov
    pytest-mock
  ];

  meta = {
    description = "A boilerplate-less updater library for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
