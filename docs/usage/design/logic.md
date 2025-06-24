# Main Logic

All the logic for your script lives in one class: an implementation of
`ABCBase` interface. See [the `base.py` source
code](https://github.com/PerchunPak/nixpkgs-updaters-library/blob/main/nupd/base.py)
for the exact interface definition.

First, you need to set two values:

- `_default_input_file`: path to the default input file.
- `_default_output_file`: path to the default output file.

Those are then may be overridden by the user of your script using the CLI
flags.

Then there are multiple methods you have to implement:

- `async get_all_entries()`: this returns a list of all possible entries for
  prefetching. This may crawl some site for a list of all packages, or read an
  input file (e.g. using [`CsvInput`] util).
- `write_entries_info()`: this simply writes
