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
    rev = "f126ffb6cdcc2cbc7e2bec8b58d27be31e3036f2";
    hash = "sha256-wbWgUK6ZSXeDguCDynizYHgV4U2+hiu6/hJLDWvDb8Y=";
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

  disabledTests = [
    # flaky in CI
    "test_write_in_background"
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
