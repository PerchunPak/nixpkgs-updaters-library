{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nix-github-actions = {
      url = "github:nix-community/nix-github-actions";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      nix-github-actions,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        inherit (self) outputs;
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ (import ./nix/overlay.nix) ];
        };
        lib = pkgs.lib;
      in
      {
        inherit pkgs;

        packages = {
          default = pkgs.callPackage ./nix/package.nix { };
          nixpkgs-updaters-library = self.packages.${system}.default;
          nupd = self.packages.${system}.default;
        };

        devShell = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = with pkgs; [
            basedpyright
            python312Packages.debugpy
            pre-commit
            ruff
          ];

          PYTHONPATH = ".";
        };
      }
    )
    // {
      githubActions = nix-github-actions.lib.mkGithubMatrix {
        checks = builtins.listToAttrs (
          map
            (system: {
              name = system;
              value.package = self.packages.${system}.default;
            })
            [
              "x86_64-linux"
              "x86_64-darwin"
              "aarch64-darwin"
            ]
        );
      };
    };
}
