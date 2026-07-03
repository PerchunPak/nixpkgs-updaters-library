{
  lib,
  fetchPypi,
  buildPythonPackage,
  hatchling,
  typing-extensions,
}:
buildPythonPackage rec {
  pname = "joblib-stubs";
  version = "1.5.3.1.20260117";
  pyproject = true;

  src = fetchPypi {
    pname = "joblib_stubs";
    inherit version;
    hash = "sha256-1CD54mY23wHhvahRv1vOmo29bbhPCK/h39uWPmZR5yQ=";
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
