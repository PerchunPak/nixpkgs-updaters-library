final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      # I will need this eventually
      nbdb = final.callPackage ./python-nbdb.nix { pythonPackages = pfinal; };
    })
  ];
}
