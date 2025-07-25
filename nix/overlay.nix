final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = pprev.nixpkgs-updaters-library.overridePythonAttrs (old: {
        version = "2.1.1.dev"; # @version
        src = ./..;

        preCheck =
          (old.preCheck or "")
          + ''
            export HOME=$(mktemp -d)
          '';
        nativeCheckInputs = old.nativeCheckInputs ++ [
          (pfinal.callPackage ./lint-hook/lint-hook.nix { })
        ];

        dependencies = with pfinal; [
          aiohttp
          frozendict
          inject
          joblib
          loguru
          platformdirs
          pydantic
          typer
        ];
      });
      joblib-stubs = pfinal.callPackage ./joblib-stubs.nix { };
    })
  ];
}
