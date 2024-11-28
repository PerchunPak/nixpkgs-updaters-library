final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      inject = final.callPackage ./python-inject.nix { pythonPackages = pfinal; };
    })
  ];

  basedpyright = prev.basedpyright.overrideAttrs (oa: rec {
    version = "1.22.0";
    src = oa.src.override {
      rev = "refs/tags/v${version}";
      hash = "sha256-/I8KCQnjFbE64h2rQuLV31IsVTQhuDxiobQwtx0HRPM=";
    };
  });
}
