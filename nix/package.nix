{
  lib,
  buildPythonPackage,
  pythonOlder,

  # build-system
  setuptools,

  # dependencies
  aiohttp,
  attrs,
  frozendict,
  inject,
  loguru,
  nbdb,
  nix-prefetch-git,
  nurl,
  platformdirs,
  typer,

  # tests
  lint-hook,
  pytestCheckHook,
  aioresponses,
  basedpyright,
  pytest-asyncio,
  pytest-cov,
  pytest-mock,
  ruff,
}:
buildPythonPackage {
  pname = "nixpkgs-updaters-library";
  version = "0.1.0";
  pyproject = true;

  disabled = pythonOlder "3.13";

  src = ./..;

  build-system = [ setuptools ];

  dependencies = [
    aiohttp
    attrs
    frozendict
    inject
    loguru
    nbdb
    nix-prefetch-git
    nurl
    platformdirs
    typer
  ];

  nativeCheckInputs = [
    lint-hook
    pytestCheckHook

    aioresponses
    basedpyright
    pytest-asyncio
    pytest-cov
    pytest-mock
    ruff
  ];

  meta = {
    description = "A boilerplate-less updater library for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
