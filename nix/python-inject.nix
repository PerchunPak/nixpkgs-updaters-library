{
  fetchFromGitHub,
  lib,
  nix-update-script,
  pythonPackages,
}:

pythonPackages.buildPythonPackage rec {
  pname = "inject";
  version = "5.2.1";
  pyproject = true;

  disabled = pythonPackages.pythonOlder "3.9";

  src = fetchFromGitHub {
    owner = "ivankorobkov";
    repo = "python-inject";
    rev = "refs/tags/v${version}";
    hash = "sha256-Ws296ESjb+a322imiRRWTS43w32rJc/7Y//OBQXOwnw=";
  };

  build-system = with pythonPackages; [
    hatchling
    hatch-vcs
  ];

  nativeCheckInputs = with pythonPackages; [
    pytestCheckHook
  ];

  pythonImportsCheck = [ "inject" ];

  passthru.updateScript = nix-update-script { };

  meta = with lib; {
    description = "Python dependency injection framework";
    homepage = "https://github.com/ivankorobkov/python-inject";
    changelog = "https://github.com/ivankorobkov/python-inject/blob/${version}/CHANGES.md";
    license = licenses.asl20;
    maintainers = with maintainers; [ perchun ];
  };
}
