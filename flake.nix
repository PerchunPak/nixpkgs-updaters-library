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
        pkgs = import nixpkgs { inherit system; };
        lib = pkgs.lib;
      in
      {
        packages = {
          default = pkgs.callPackage ./package.nix { };
          nixpkgs-updaters-library = outputs.packages.${system}.default;
          nupd = outputs.packages.${system}.default;
        };

        devShell = pkgs.mkShell {
          buildInputs = [ outputs.packages.${system}.default ];
        };
      }
    );
}
