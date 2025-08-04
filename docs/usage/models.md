# Models

You need to implement some interfaces for the library to work. Note that the
library is generally designed to be minimalistic: you choose what to store.
This way, the library can be used for anything from simple git repositories to
GNOME extensions.

Look at [the `models.py` file](https://github.com/PerchunPak/nixpkgs-updaters-library/blob/main/nupd/models.py)
for exact details.

## `EntryInfo`

A minimal amount of information that is only enough to prefetch the entry. It
is enough to implement only these two simple attributes:

- `id`: a valid Nix key by which plugin then will be referenced. Note that this
  must be a property, so we can implement (for example) aliases.
- `async fetch()`: a method which fetches all the information required and
  returns an `Entry` instance.

## `Entry`

All information about the entry, that we need to generate Nix code.

- `minify()`: minifies all the information about the entry to an `MiniEntry`
  instance.

Also note that an `Entry` instance always has `info` field, which links to
`EntryInfo` from which this entry was fetched.

## `MiniEntry`

Minified prefetched entry with the minimal set of the required keys. This
exists with a goal to not bloat your output file with unused information.
However, it still must have enough information to reconstruct an `EntryInfo`
instance (there is an `info` field for this).
