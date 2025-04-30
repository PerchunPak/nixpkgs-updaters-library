# nixpkgs-updaters-library

[![Support Ukraine](https://badgen.net/badge/support/UKRAINE/?color=0057B8&labelColor=FFD700)](https://www.gov.uk/government/news/ukraine-what-you-can-do-to-help)

[![Build Status](https://github.com/PerchunPak/nixpkgs-updaters-library/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/PerchunPak/nixpkgs-updaters-library/actions?query=workflow%3Atest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python support versions badge (from pypi)](https://img.shields.io/pypi/pyversions/nixpkgs-updaters-library)](https://www.python.org/downloads/)

A boilerplate-less updater library for Nixpkgs ecosystems, that aims to replace
[`pluginupdate.py`](https://github.com/NixOS/nixpkgs/blob/76d002f98bff2df45147d02d828315aeab934da7/maintainers/scripts/pluginupdate-py/pluginupdate.py).

If you want to know more, I wrote an entire draft RFC for this (but commenters
told me to just write the library):

- https://discourse.nixos.org/t/new-rfc-draft-standardize-updater-scripts-successor-of-rfc-109/54290

Feel free to reach out to me if you have any questions/concerns/requests for
features.

## Quick tour

The main design idea is that you implement your ecosystem-specifics, and this
library handles all boilerplate it could possible handle, while still being not
too specific.

### Terms

- The library — this package.
- An updater script — this is what you would run to add/update plugins in
  specific ecosystems.
- An input — list of references to the outputs. As an example, for Vim plugins,
  this would be a CSV table with GitHub URLs and other data.
- An output — what is generated at the end. This can be for example a plugin or
  an extension.
- An entry — a single unit of what updater updates. For Vim plugins this would
  be a plugin, for Gnome extensions this would be an extension.

### Technical details

Generally you have to implement three classes:
- `EntryInfo`: information about the entry. This must include only information
  that is stored in your input file (e.g. a CSV table) and it is used to fetch
  your output data.
- `Entry`: fetched information about the entry. You cannot have here some hanging
  information (e.g. commit is None means use latest commit).
- `ABCBase`: your ecosystem specific functions.

The design is intentionally done this way, so you have either nothing but a URL
for a prefetch or completely fetched everything. Look at `examples/simple` and
[`examples/vim-plugins`](https://github.com/PerchunPak/nixpkgs-updaters-library/tree/vim-plugins-updater/example/vim-plugins)
for a complete implementation of everything.
