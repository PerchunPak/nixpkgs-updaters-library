# nixpkgs-updaters-library

[![Support Ukraine](https://badgen.net/badge/support/UKRAINE/?color=0057B8&labelColor=FFD700)](https://www.gov.uk/government/news/ukraine-what-you-can-do-to-help)

[![Build Status](https://github.com/PerchunPak/nixpkgs-updaters-library/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/PerchunPak/nixpkgs-updaters-library/actions?query=workflow%3Atest)
[![Documentation Build Status](https://readthedocs.org/projects/nixpkgs-updaters-library/badge/?version=latest)](https://nixpkgs-updaters-library.readthedocs.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python support versions badge (from pypi)](https://img.shields.io/pypi/pyversions/nixpkgs-updaters-library)](https://www.python.org/downloads/)

Library for nixpkgs plugin updaters

## Features

- Free! We don't want any money from you!
- Add yours!

## Installing

```bash
pip install nixpkgs-updaters-library
```

## Installing for local developing

```bash
git clone https://github.com/PerchunPak/nixpkgs-updaters-library.git
cd nixpkgs-updaters-library
```

### Installing `poetry`

Next we need install `poetry` with [recommended way](https://python-poetry.org/docs/master/#installation).

If you use Linux, use command:

```bash
curl -sSL https://install.python-poetry.org | python -
```

If you use Windows, open PowerShell with admin privileges and use:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Installing dependencies

```bash
poetry install --no-dev
```

### Configuration

All configuration happens in `config.yml`, or with environment variables.

### If something is not clear

You can always write me!

## Example

```py
from nixpkgs_updaters_library.example import some_function

print(some_function(3, 4))
# => 7
```

## Updating

```bash
pip install -U nixpkgs-updaters-library
```

### For local development

For updating, just re-download repository (do not forget save config),
if you used `git` for downloading, just run `git pull`.

## Thanks

This project was generated with [python-template](https://github.com/PerchunPak/python-template).
