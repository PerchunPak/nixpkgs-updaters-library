{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        inherit (self) outputs;
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
                (pfinal: pprev: {
                  inject = final.callPackage ./nix/python-inject.nix { pythonPackages = pfinal; };
                })
              ];
            })
          ];
        };
        lib = pkgs.lib;
      in
      {
        inherit pkgs;

        packages = {
          default = pkgs.callPackage ./nix/package.nix { };
          nixpkgs-updaters-library = outputs.packages.${system}.default;
          nupd = outputs.packages.${system}.default;
        };

        devShell = pkgs.mkShell {
          inputsFrom = [ outputs.packages.${system}.default ];

          PYTHONPATH = ".";
        };
      }
    );
}
