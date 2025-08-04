# nixpkgs-updaters-library

[![Support Ukraine](https://badgen.net/badge/support/UKRAINE/?color=0057B8&labelColor=FFD700)](https://www.gov.uk/government/news/ukraine-what-you-can-do-to-help)
[![Tests Status](https://github.com/PerchunPak/nixpkgs-updaters-library/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/PerchunPak/nixpkgs-updaters-library/actions?query=workflow%3Atest)

A boilerplate-less updater library for Nixpkgs bulk updaters.

The goal of this library is for you to write a simple script, that implements
a few abstract methods and classes, and get a powerful bulk updater in the
result.

> [!IMPORTANT]
> All code in this library was written by a human.
>
> (you can still submit AI code in a PR, but it will be heavily reviewed and
> would get a lot of scepticism)

## Why?

Sometimes, there are types of packages, that are very simplistic to package. As
an example we can take Vim plugins, (mostly) to package a plugin it is just
enough to download a Git repository.

```nix
buildVimPlugin {
  pname = "lazy.nvim";
  version = "2025-02-25";
  src = fetchFromGitHub {
    owner = "folke";
    repo = "lazy.nvim";
    rev = "6c3bda4aca61a13a9c63f1c1d1b16b9d3be90d7a";
    hash = "sha256-nQ8PR9DTdzg6Z2rViuVD6Pswc2VvDQwS3uMNgyDh5ls=";
  };
};
```

Now imagine we have a thousand of such plugins, writing out a package for each
of them separately and then also keeping this up to date would be awful.

This library allows you to easily manage unlimited amount of packages. Before
this became a thing, many would just write a Python script with all the logic
from the ground up. Later, when we would want to add a feature to such
a script, it would grow in complexity and result into a nightmare code.

By using the library, we can avoid a lot of boilerplate and get many powerful
features for free. As an example, single-plugin update (when you want to update
only one plugin instead of all of them).

## Usage

Please consult our [documentation](https://nupd.perchun.it) for that.
