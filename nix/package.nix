{
  lib,
  python3Packages,
}:
python3Packages.buildPythonPackage {
  pname = "nixpkgs-updaters-library";
  version = "0.1.0";
  pyproject = true;

  src = ./..;

  build-system = with python3Packages; [ setuptools ];

  nativeCheckInputs = with python3Packages; [
    pytestCheckHook
    pytest-asyncio
    pytest-cov
    pytest-mock
    aioresponses
  ];

  dependencies = with python3Packages; [
    aiohttp
    attrs
    inject
    loguru
    platformdirs
    typer
    nbdb
  ];

  meta = {
    description = "A boilerplate-less updater for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
