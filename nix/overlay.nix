final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pfinal: pprev: {
      nixpkgs-updaters-library = pprev.nixpkgs-updaters-library.overridePythonAttrs (old: {
        version = "3.1.1.dev"; # @version
        src = ./..;

        preCheck = (old.preCheck or "") + ''
          export HOME=$(mktemp -d)
          export PYTHONPATH=".:$PYTHONPATH"
          rm -rf docs/
        '';
        nativeCheckInputs = (final.lib.lists.remove pfinal.pytest-cov-stub old.nativeCheckInputs) ++ [
          (pfinal.callPackage ./lint-hook/lint-hook.nix { })
          pfinal.pytest-cov
        ];

        dependencies = with pfinal; [
          aiohttp
          cyclopts
          frozendict
          inject
          joblib
          loguru
          platformdirs
          pydantic
        ];
      });
      joblib-stubs = pfinal.callPackage ./joblib-stubs.nix { };
    })
  ];
}
