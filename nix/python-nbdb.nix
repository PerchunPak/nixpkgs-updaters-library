{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  nix-update-script,

  # build-system
  poetry-core,
  poetry-dynamic-versioning,

  # dependencies
  aiofile,
  typing-extensions,

  # tests
  pytestCheckHook,
  pytest-asyncio,
  pytest-cov,
  pytest-mock,
  pytest-randomly,
  faker,
}:

buildPythonPackage rec {
  pname = "nbdb";
  version = "0.1.2";
  pyproject = true;

  # tests do crash often in CI on python 3.13
  enableParallelBuilding = false;

  src = fetchFromGitHub {
    owner = "PerchunPak";
    repo = "nonbloat-db";
    rev = "refs/tags/v${version}";
    hash = "sha256-WFN7rJec1jviP39S2LlhVxqB2GQVbm3jm1b+KXkHoYM=";
  };

  build-system = [
    poetry-core
    poetry-dynamic-versioning
  ];

  dependencies = [
    aiofile
    typing-extensions
  ];

  nativeCheckInputs = [
    pytestCheckHook
    pytest-asyncio
    pytest-cov
    pytest-mock
    pytest-randomly
    faker
  ];

  pythonImportsCheck = [
    "nbdb"
    "nbdb.storage"
  ];

  passthru.updateScript = nix-update-script { };

  meta = {
    description = "Simple key-value database for my small projects!";
    homepage = "https://github.com/PerchunPak/nonbloat-db";
    changelog = "https://github.com/PerchunPak/nonbloat-db/blob/v${version}/CHANGES.md";
    license = lib.licenses.agpl3Only;
    maintainers = with lib.maintainers; [ perchun ];
  };
}
