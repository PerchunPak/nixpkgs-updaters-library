{
  lib,
  buildPythonPackage,
  pythonOlder,

  # build-system
  setuptools,

  # dependencies
  aiohttp,
  attrs,
  inject,
  loguru,
  platformdirs,
  typer,
  nbdb,

  # tests
  pytestCheckHook,
  pytest-asyncio,
  pytest-cov,
  pytest-mock,
  aioresponses,
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
    inject
    loguru
    platformdirs
    typer
    nbdb
  ];

  nativeCheckInputs = [
    pytestCheckHook
    pytest-asyncio
    pytest-cov
    pytest-mock
    aioresponses
  ];

  meta = {
    description = "A boilerplate-less updater library for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
