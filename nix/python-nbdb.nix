{
  fetchFromGitHub,
  lib,
  nix-update-script,
  pythonPackages,
}:

pythonPackages.buildPythonPackage rec {
  pname = "nbdb";
  version = "0.1.1";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "PerchunPak";
    repo = "nonbloat-db";
    rev = "refs/tags/v${version}";
    hash = "sha256-hSErNsGmKK56+anGNmghLX6Vkn7gtVhokBS69fGoAIw=";
  };

  build-system = with pythonPackages; [
    poetry-core
    poetry-dynamic-versioning
  ];

  dependencies = with pythonPackages; [
    aiofile
    typing-extensions
  ];

  nativeCheckInputs = with pythonPackages; [
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
