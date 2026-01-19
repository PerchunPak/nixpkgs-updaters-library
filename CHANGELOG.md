# Changelog

We follow [Semantic Versions](https://semver.org/) style.

<!-- @version -->

## Version 3.1.1

Fixed tests, only internal changes.

## Version 3.1.0

- Added support for updating entries by their IDs ([`c1104d3`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/c1104d3c6bc5b5c893084078491ed45689cf4451))

  If we take Vim plugins as an example:

  ```sh
  # instead of using
  vim-plugins-updater update 'https://github.com/folke/lazy.nvim/'
  # you can now just reference the plugin's name!
  vim-plugins-updater update lazy-nvim
  ```

## Version 3.0.0

I have finally written documentation! The PR is #5 and you can preview them at
https://nupd.perchun.it/. It ain't much but it's honest work.

### Breaking changes

- Replace custom cache with custom DB by joblib ([`305ace8`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/305ace8459c643e8bc3d2b11557ae5724eda2dc4))

  Previous, we used homemade caching with a database I wrote. It was very flaky,
  so we switched to [joblib](https://joblib.readthedocs.io/en/stable/memory.html) instead.

- nix_prefetch_url: change default value of unpack to False ([`aca2393`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/aca239339042e1991891cdb4932116d9ac04e9a2))

  It is different from CLI's default which makes it confusing

### Small changes

- Accept any PathLike as a Path argument ([`428926e`](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/428926eec56385fb9b4f61066433ade223382339))
- [All code in this library was written by a human.](https://github.com/PerchunPak/nixpkgs-updaters-library/commit/9fe43a17cc8cebc5cf8f125ee5909a42a44f941f)

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
