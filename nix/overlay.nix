final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = import ./package.nix final pfinal pprev;
      joblib-stubs = pfinal.callPackage ./joblib-stubs.nix { };

      # remove the overlay when the package in nixpkgs gets updated
      cyclopts = pprev.cyclopts.overridePythonAttrs (
        old:
        assert old.version == "4.17.0";
        {
          version = "4.18.0";
          src = final.fetchFromGitHub {
            owner = "BrianPugh";
            repo = "cyclopts";
            tag = "v4.18.0";
            hash = "sha256-Gg1FrEXmx90U5vO6u0ttue+niswIuWrKYFpscAoaaKY=";
          };
        }
      );
    })
  ];
}
