# Quick Start

Let's together create a simple example script, which loads GitHub URLs from an
`input.csv` file and outputs prefetched last commit and hashes to an
`output.json` files.

You can view the full code in the
[`example/simple`](https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple)
directory.

First, we need to implement [our models](./design/models.md).

```py title="script.py"
from nupd.models import EntryInfo, Entry
from nupd.fetchers.github import GHRepository
from nupd.fetchers.nurl import NurlResult

class MyEntryInfo(EntryInfo, frozen=True):
    owner: str
    repo: str

    @property# (1)!
    def id(self) -> str:
        return self.repo

    async def fetch(self) -> MyEntry:
        # we will implement this later

class MyEntry(Entry[EntryInfo, MyMiniEntry], frozen=True):
    info: MyEntryInfo
    fetched: GHRepository
    nurl_result: NurlResult
```

1. This is a property, because we could implement e.g. aliases

Wait, what is `GHRepository` and `NurlResult`? Nupd implements a bunch of
helpers for you! This includes an easy fetcher for GitHub repositories and
a wrapper around [nurl](https://github.com/nix-community/nurl).
