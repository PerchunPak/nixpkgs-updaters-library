# nixpkgs-updaters-library

[![Support Ukraine](https://badgen.net/badge/support/UKRAINE/?color=0057B8&labelColor=FFD700)](https://www.gov.uk/government/news/ukraine-what-you-can-do-to-help)

[![Build Status](https://github.com/PerchunPak/nixpkgs-updaters-library/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/PerchunPak/nixpkgs-updaters-library/actions?query=workflow%3Atest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python support versions badge (from pypi)](https://img.shields.io/pypi/pyversions/nixpkgs-updaters-library)](https://www.python.org/downloads/)

A boilerplate-less updater library for Nixpkgs ecosystems, that aims to replace
[`pluginupdate.py`](https://github.com/NixOS/nixpkgs/blob/76d002f98bff2df45147d02d828315aeab934da7/maintainers/scripts/pluginupdate-py/pluginupdate.py).

This is still very work and progress, but for more context you can check out:

- https://discourse.nixos.org/t/new-rfc-draft-standardize-updater-scripts-successor-of-rfc-109/54290
- https://github.com/NixOS/nixpkgs/pull/336137

Feel free to reach out to me if you have any questions/concerns/requests for
features.

## TODO

- [x] Sourcehut does not support fetching the latest revision???
- [ ] Cache invalidation
- [ ] progress bar
- [ ] Duplicate plugins?
- [ ] Documentation
- [ ] Some abstract class for implementing redirects

## Known bugs

- If GitHub repository has multiple licenses, GitHub API will show only the first one.
- Subprojects on GitLab are not supported
- Some Git hosts are not supported yet, e.g. Sourcehut
