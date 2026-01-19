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
        inherit (pkgs) lib;

        pkgs = import nixpkgs {
          inherit system;
          overlays = [ (import ./nix/overlay.nix) ];
        };
      in
      {
        inherit pkgs;

        packages = {
          default = pkgs.python3Packages.nixpkgs-updaters-library;
          nixpkgs-updaters-library = self.packages.${system}.default;
          nupd = self.packages.${system}.default;
        };

        devShell = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = with pkgs; [
            basedpyright
            python3Packages.debugpy
            python3Packages.joblib-stubs
            ruff

            nurl
            nix-prefetch-scripts

            # docs
            python3Packages.mkdocs-material
            python3Packages.mkdocs-github-admonitions-plugin
            python3Packages.mkdocstrings
            python3Packages.mkdocstrings-python
          ];

          PYTHONPATH = ".";
        };
      }
    )
    // {
      githubActions = nix-github-actions.lib.mkGithubMatrix {
        checks = self.packages;
        platforms = {
          "x86_64-linux" = "ubuntu-24.04";
          "aarch64-linux" = "ubuntu-24.04-arm";
          "x86_64-darwin" = "macos-15-intel";
          "aarch64-darwin" = "macos-15";
        };
      };
    };
}
