{
  lib,
  fetchPypi,
  buildPythonPackage,
  hatchling,
  typing-extensions,
}:
buildPythonPackage rec {
  pname = "joblib-stubs";
  version = "1.5.0.1.20250510";
  pyproject = true;

  src = fetchPypi {
    pname = "joblib_stubs";
    inherit version;
    hash = "sha256-jZsGD/3HMV4f3dXi1AfwelPauL3GHJ+3j+CEG7+vMIw=";
  };

  build-system = [
    hatchling
  ];

  dependencies = [
    typing-extensions
  ];

  meta = {
    description = "Joblib stubs";
    homepage = "https://pypi.org/project/joblib-stubs/";
    license = lib.licenses.mit;
  };
}
