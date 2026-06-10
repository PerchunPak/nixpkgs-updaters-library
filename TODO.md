# TODO

## Code

- [x] Sourcehut does not support fetching the latest revision???
- [x] Test fetching specific branch
- [x] ``nix-prefetch-url`` should have ``unpack`` default to False
- [x] ``nix-prefetch-git`` has ``--quiet``, which we should always provide
- [x] Check that IDs are equal
- [x] Cache invalidation
- [x] cyclopts
- [x] progress bar
- [ ] Some abstraction for implementing redirects & deprecations
- [x] Use semaphores instead of chunks
- [x] nurl FETCHERS | str
- [x] Auto commit
- [ ] AIOHttp session pooling
- [ ] Handle errors in `fetch_entries`
- [ ] Reduce mocking in tests
- [ ] Explore nix vs json vs yaml evaluation speed and file size

## Docs

- [x] import README.md to index.rst
- [ ] Separate page for main branch and stable releases?

## Vim plugins updater

- [ ] Support `fetchgit`
- [ ] Plugin renames
- [ ] Fetching latest git tags
  - [x] Fetch latest release
  - [ ] Update to tag only if current version is older
