final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nbdb = final.callPackage ./python-nbdb.nix { pythonPackages = pfinal; };
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
