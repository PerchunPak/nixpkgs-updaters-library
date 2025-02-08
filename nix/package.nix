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

  build-system = [ hatchling ];

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
