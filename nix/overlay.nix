final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = import ./package.nix final pfinal pprev;
      joblib-stubs = pfinal.callPackage ./joblib-stubs.nix { };

      cyclopts = pprev.cyclopts.overridePythonAttrs (
        old:
        # remove the patch when the package in nixpkgs gets updated
        # https://github.com/NixOS/nixpkgs/pull/530049
        assert old.version == "4.16.1";
        {
          patches = old.patches or [ ] ++ [
            (final.fetchpatch2 {
              url = "https://github.com/BrianPugh/cyclopts/pull/833.diff";
              hash = "sha256-i2+RVrkF5dL8A+LFKmOwWYBrlXYGcFsJRIRWngc5e38=";
            })
          ];
        }
      );
    })
  ];
}
