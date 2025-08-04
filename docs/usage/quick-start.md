# Quick Start

Let's together create a simple example script, which loads GitHub URLs from an
`input.csv` file, and outputs last commit plus hashes to an `output.json` file.

You can view the full code in the
[`example/simple`](https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple)
directory.

First, we need to implement [our models](./models.md).

```py title="script.py"
from __future__ import annotations

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
helpers for you! This includes an [easy fetcher for GitHub
repositories](./helpers/github.md) and [a wrapper](./helpers/nurl.md) around
[nurl](https://github.com/nix-community/nurl) - THE prefetcher for Nix
ecosystem.

We should also implement [`MiniEntry`](./models.md#minientry),
which is just a minified version of our
[`Entry`](./models.md#entry) to not bloat the result file with
unnecessary information:

```py title="script.py"
class MyEntry:
    # ...

    @t.override
    def minify(self) -> MyMiniEntry:
        return MyMiniEntry(
            info=self.info,
            nurl=self.nurl_result,
        )

class MyMiniEntry(MiniEntry[MyEntryInfo], frozen=True):
    nurl: nurl.NurlResult
```

## Implement core logic

!!! danger

    This section includes some nasty Python typing shenanigans, so don't worry
    if you are overwhelmed - just copy-paste and hope it works! You can also
    consult me about anything if you need help with this library (just open
    a [GitHub discussion](https://github.com/PerchunPak/nixpkgs-updaters-library/discussions))

    Though those shenanigans are very useful: with them, every single step in
    the library is strongly typed. Also, do note: **everything you put into
    models gets automatically validated**.

    If you want to type-check your script, I recommend using
    [basedpyright](https://github.com/DetachHead/basedpyright) (this is what
    I use for this library).

```py title="script.py"
import dataclasses
import typing as t
from pathlib import Path

from nupd.base import ABCBase

if t.TYPE_CHECKING:
    import collections.abc as c

ROOT = Path(__file__).parent
if "/nix/store" in str(ROOT):
    # we are bundled using nix, use working directory instead of root
    ROOT = Path.cwd()


@dataclasses.dataclass
class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
    # Due to some implementation details, we cannot provide custom arguments
    # definitions for existing commands (however you can implement new
    # commands!), we have to provide default values for input and output files
    # this way.
    _default_input_file: Path = dataclasses.field(
        init=False, default=ROOT / "input.csv"# (1)!
    )
    _default_output_file: Path = dataclasses.field(
        init=False, default=ROOT / "output.json"
    )
```

1. If you want to provide a path to nixpkgs, you can do so using
   `nupd.utils.NIXPKGS_PLACEHOLDER / "your" / "path" / "file.csv"`.
   This will automatically use the nixpkgs path provided in CLI the flag.

There are only 3 methods we have to implement to get access to all the features:

::: nupd.base.ABCBase.get_all_entries

```py title="script.py"
    @t.override# (1)!
    async def get_all_entries(self) -> c.Iterable[MyEntryInfo]:
        return CsvInput[MyEntryInfo](self.input_file).read(
            lambda x: MyEntryInfo(**x)
        )
```

1. This just means that we are overriding a method from parent class. You can
   safely remove everything that is connected with `typing` module, if you
   don't want to type-check (though I strongly don't recommend that)

Note that this method is async, so you can implement reading a list of packages
as an HTTP request to central package distribution center (e.g. PyPi), if it
makes sense of course.

::: nupd.base.ABCBase.write_entries_info

```py title="script.py"
    @t.override
    def write_entries_info(self, entries_info: c.Iterable[MyEntryInfo]) -> None:
        CsvInput[MyEntryInfo](self.input_file).write(
            entries_info,
            serialize=lambda x: x.model_dump(mode="json"),
        )
```

::: nupd.base.ABCBase.parse_entry_id

```py title="script.py"
    @t.override
    def parse_entry_id(self, to_parse: str) -> MyEntryInfo:
        split = to_parse.split("/")
        if len(split) != 2:
            raise InvalidArgumentError(
                f"Invalid value passed: {to_parse!r}. "
                "Should be something like 'owner/repo'"
            )

        owner, repo = split
        return MyEntryInfo(owner=owner, repo=repo)
```

## Boilerplate

At last, we have to write some amount of boilerplate:

```py title="script.py"
if __name__ == "__main__":# (1)!
    assert isinstance(app.info.context_settings, dict)
    app.info.context_settings["obj"] = ImplClasses(
        base=MyImpl,
        mini_entry=MyMiniEntry,
        entry=MyEntry,
        entry_info=MyEntryInfo,
    )

    app()
```

1. If you don't know what is it:
   [https://stackoverflow.com/a/419185](https://stackoverflow.com/a/419185)

The `app.info.context_settings["obj"]` block is how we point out what
implementation classes we use.

## Let's run the actual script

You can view the full script
[here](https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple).
But before running our creation, we have to create `input.csv`:

```csv title="input.csv"
owner,repo
nvim-treesitter,nvim-treesitter
folke,todo-comments.nvim
tpope,vim-surround
```

And, finally, let's run the script!

```
$ python script.py --log-level debug update
2025-07-01 18:24:15.568 | DEBUG    | nupd.logs:setup_logging:50 - Logging was setup!
2025-07-01 18:24:15.569 | INFO     | nupd.base:fetch_entries:134 - Going to fetch 3 entries with the limit of 32 simultaneously
2025-07-01 18:24:15.569 | DEBUG    | nupd.base:fetch_entries:141 - Next chunk (3)
2025-07-01 18:24:15.569 | DEBUG    | __main__:fetch:43 - Fetching tpope/vim-surround
2025-07-01 18:24:15.573 | DEBUG    | __main__:fetch:43 - Fetching folke/todo-comments.nvim
2025-07-01 18:24:15.573 | DEBUG    | __main__:fetch:43 - Fetching nvim-treesitter/nvim-treesitter
2025-07-01 18:24:17.179 | DEBUG    | nupd.fetchers.nurl:nurl:58 - Running nurl on https://github.com/folke/todo-comments.nvim
2025-07-01 18:24:17.410 | DEBUG    | nupd.fetchers.nurl:nurl:58 - Running nurl on https://github.com/tpope/vim-surround
2025-07-01 18:24:17.572 | DEBUG    | nupd.fetchers.nurl:nurl:58 - Running nurl on https://github.com/nvim-treesitter/nvim-treesitter
2025-07-01 18:24:19.257 | SUCCESS  | nupd.base:update_cmd:125 - Successfully updated 3 entries!
```

It is that simple! Now, let's check out our `output.json`:

```json title="output.json"
{
  "nvim-treesitter": {
    "info": {
      "owner": "nvim-treesitter",
      "repo": "nvim-treesitter"
    },
    "nurl": {
      "args": {
        "hash": "sha256-ZQ3HJ3dhtMS75GpW9xxt/ERjqD6v/Fzw+NLyml2EuYM=",
        "owner": "nvim-treesitter",
        "repo": "nvim-treesitter",
        "rev": "c1efc9a9058bb54cfcb6f0a4fc14a4ac8a66bdaa"
      },
      "fetcher": "fetchFromGitHub"
    }
  },
  "todo-comments.nvim": {
    "info": {
      "owner": "folke",
      "repo": "todo-comments.nvim"
    },
    "nurl": {
      "args": {
        "hash": "sha256-at9OSBtQqyiDdxKdNn2x6z4k8xrDD90sACKEK7uKNUM=",
        "owner": "folke",
        "repo": "todo-comments.nvim",
        "rev": "304a8d204ee787d2544d8bc23cd38d2f929e7cc5"
      },
      "fetcher": "fetchFromGitHub"
    }
  },
  "vim-surround": {
    "info": {
      "owner": "tpope",
      "repo": "vim-surround"
    },
    "nurl": {
      "args": {
        "hash": "sha256-DZE5tkmnT+lAvx/RQHaDEgEJXRKsy56KJY919xiH1lE=",
        "owner": "tpope",
        "repo": "vim-surround",
        "rev": "3d188ed2113431cf8dac77be61b842acb64433d9"
      },
      "fetcher": "fetchFromGitHub"
    }
  }
}
```
