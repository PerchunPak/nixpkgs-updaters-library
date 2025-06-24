# Quick Start

Let's together create a simple example script, which loads GitHub URLs from an
`input.csv` file, outputs prefetched last commit and hashes to an
`output.json` files.

You can view the full code in the
[`example/simple`](https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple)
directory.

First, we need to implement [our models](./design/models.md).

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

Then we can start implementing the core logic

!!! warning

    The next part of this page includes some nasty Python typing shenanigans,
    so don't worry if you are overwhelming - just copy-paste and hope it works!
    You can also consult me about anything if you need help with this library
    (just open a [GitHub
    discussion](https://github.com/PerchunPak/nixpkgs-updaters-library/discussions))

    Thought those shenanigans are very useful! With them, every single step in
    the library is strongly typed, and do note, that everything you put into
    models gets automatically validated.

    If you want to type-check your script, I recommend using
    [basedpyright](https://github.com/DetachHead/basedpyright)
    (this is what I use for this library).

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
    _default_input_file: Path = dataclasses.field(
        init=False, default=ROOT / "input.csv"
    )# (1)!
    _default_output_file: Path = dataclasses.field(
        init=False, default=ROOT / "output.json"
    )# (1)!
```

1. Due to some implementation details, we cannot provide custom arguments
   definitions for existing commands (however you can implement new commands!),
   we have to provide default values for input and output files this way.

There are only 3 methods we have to implement to get access to all the features:

!!! tip

    `G` prefix means it is a [Generic](https://typing.python.org/en/latest/reference/generics.html).

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
