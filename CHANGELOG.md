# Changelog

We follow [Semantic Versions](https://semver.org/) style.

<!-- @version -->

## Version 2.1.1

- Fix a bug where `has_submodules` in nurl result is an int ([`eac5c4f7`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/eac5c4f7b5ad8c471ed866e3f1fc967f65a0676d))

## Version 2.1.0

- Sanitize strings during GitHub fetching ([`23f072a7`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/23f072a7313c90ac25b5eb50a56de58d76689de1))

## Version 2.0.0

- Rewrite everything to use [`pydantic`](https://pypi.org/project/pydantic/) instead of [`attrs`](https://pypi.org/project/attrs/) ([#3](https://github.com/PerchunPak/nixpkgs-updaters-library/pull/3))

  Pydantic does runtime type validation and is better for our usecase. While
  attrs doesn't have any sensible way to recursively serialize/deserialize into
  JSON. This is so stupid.

- Minify output file before writing it ([`2241739b`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/2241739bc8ff7d25f4404a8a6305fed9659888fd))

  This is one of the required features to migrate Vim plugins updater.

## Version 1.2.0

- Show `--help` if no arguments were provided ([`687c0859`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/687c08596302b525a136d6ff66ccaf9f8147f450))

- Fetch latest version (release or tag) of the GitHub repository ([#2](https://github.com/PerchunPak/nixpkgs-updaters-library/pull/2), [`7bb88bab`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/7bb88bab8c9dffdcf5116d6c4f46094d76c511a2))

## Version 1.1.0

- Fetch whether the repository has submodules ([`67978b9e`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/67978b9ea46025c90f0b39e12e21c89ae4c9f72e))

## Version 1.0.2

- Added a centralized place to define executables, so it is easier to patch it from Nix ([`db1f608e`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/db1f608e725d45f35e0082b666fbdb4af96ceeb6))

## Version 1.0.1

- Switched building system to hatchling, because setuptools didn't look for code recursively ([`8691eb50`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/8691eb50dc2dd0a6087fb5a26717bd676c87295c))


## Version 1.0.0

This is the initial stable release, though it is still bare-bones, but the core functionality works. Look at README.md for more details
