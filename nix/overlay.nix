final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = pfinal.callPackage ./package.nix { };
      nbdb = pfinal.callPackage ./python-nbdb.nix { };

      lint-hook = pfinal.callPackage ./lint-hook/lint-hook.nix { };
    })
  ];
}
