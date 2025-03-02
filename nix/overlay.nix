final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = pprev.nixpkgs-updaters-library.overridePythonAttrs (old: {
        version = "1.2.0.dev"; # @version
        src = ./..;
        nativeCheckInputs = old.nativeCheckInputs ++ [
          (pfinal.callPackage ./lint-hook/lint-hook.nix { })
        ];

        dependencies = with pfinal; [
          aiohttp
          frozendict
          inject
          loguru
          nonbloat-db
          platformdirs
          pydantic
          typer
        ];
      });
    })
  ];
}
