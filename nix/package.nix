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
  aioresponses,
  basedpyright,
  pytest-asyncio,
  pytest-cov,
  pytest-mock,
  pytestCheckHook,
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
    inject
    loguru
    platformdirs
    typer
    nbdb
  ];

  nativeCheckInputs = [
    aioresponses
    basedpyright
    pytest-asyncio
    pytest-cov
    pytest-mock
    pytestCheckHook
    ruff
  ];

  installCheckPhase = ''
    echo Running linter
    ruff check --show-fixes --exit-non-zero-on-fix .

    echo Running formatter
    ruff format --diff .

    echo Running basedpyright
    basedpyright .
  '';

  meta = {
    description = "A boilerplate-less updater library for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
