{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    nix-github-actions = {
      url = "github:nix-community/nix-github-actions";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nix-github-actions,
      ...
    }:
    let
      inherit (self) outputs;
      inherit (nixpkgs) lib;

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems =
        function:
        lib.genAttrs systems (
          system:
          function (
            import nixpkgs {
              inherit system;
              overlays = [ (import ./nix/overlay.nix) ];
            }
          )
        );
    in
    {
      pkgs = forAllSystems (x: x);

      packages = forAllSystems (
        pkgs:
        let
          inherit (pkgs.stdenv.hostPlatform) system;
        in
        {
          default = pkgs.python3Packages.nixpkgs-updaters-library;
          nixpkgs-updaters-library = self.packages.${system}.default;
          nupd = self.packages.${system}.default;
        }
      );

      devShell = forAllSystems (
        pkgs:
        let
          inherit (pkgs.stdenv.hostPlatform) system;
        in
        pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = with pkgs; [
            basedpyright
            python3Packages.debugpy
            python3Packages.joblib-stubs
            ruff

            nurl
            nix-prefetch-scripts
            nix-prefetch-github

            # docs
            python3Packages.furo
            python3Packages.sphinx
            python3Packages.sphinx-autobuild
            python3Packages.sphinx-autodoc-typehints
          ];

          shellHook = ''
            export PYTHONPATH=$PWD:$PYTHONPATH
          '';
        }
      );

      githubActions = nix-github-actions.lib.mkGithubMatrix {
        checks = lib.mapAttrs (n: v: { inherit (v) nixpkgs-updaters-library; }) self.packages;
        platforms = {
          "x86_64-linux" = "ubuntu-26.04";
          "aarch64-linux" = "ubuntu-26.04-arm";
          "aarch64-darwin" = "macos-26";
        };
      };
    };
}
