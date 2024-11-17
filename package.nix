{
  lib,
  python3Packages,
}:
python3Packages.buildPythonPackage {
  pname = "nixpkgs-updaters-library";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  build-system = with python3Packages; [ setuptools ];

  dependencies = with python3Packages; [
    aiohttp
    attrs
    typer
  ];

  meta = {
    description = "A boilerplate-less updater for Nixpkgs ecosystems";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
