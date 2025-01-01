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
  version = "0.1.3";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "PerchunPak";
    repo = "nonbloat-db";
    tag = "v${version}";
    hash = "sha256-eYYLXs8Uk1LH3VvLqe8IkzsotNFFV3ZKsT/UjXIJuow=";
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
