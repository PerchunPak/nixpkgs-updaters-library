final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = pfinal.callPackage ./package.nix { };
      nbdb = pfinal.callPackage ./python-nbdb.nix { };
      loguru = pfinal.callPackage ./python-loguru.nix { };

      inject = pprev.inject.overrideAttrs (old: {
        patches = (old.patches or [ ]) ++ [
          (final.fetchpatch2 {
            url = "https://patch-diff.githubusercontent.com/raw/ivankorobkov/python-inject/pull/110.diff";
            hash = "sha256-T98p9zK+U14pR5ybzIxl3jrn78jmwCJNQWg+HcyO4dc=";
          })
        ];
      });
    })
  ];
}
