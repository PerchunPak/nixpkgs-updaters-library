import collections.abc as c
import os
import typing as t
from pathlib import Path

import inject
from attrs import define

from nupd.base import ABCBase
from nupd.cli import app
from nupd.fetchers.github import (
    GHRepository,
    github_fetch_graphql,
    github_fetch_rest,
)
from nupd.injections import Config
from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo, ImplClasses

ROOT = Path(__file__).parent
INPUT_FILE = ROOT / "input.txt"
OUTPUT_FILE = ROOT / "output.json"


@define(frozen=True)
class MyEntry(Entry):
    fetched: GHRepository


@define(frozen=True)
class MyEntryInfo(EntryInfo):
    owner: str
    repo: str

    @t.override
    async def fetch(self) -> MyEntry:
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token is not None:
            result = await github_fetch_graphql(
                self.owner, self.repo, github_token
            )
        else:
            result = await github_fetch_rest(
                self.owner, self.repo, github_token=None
            )

        # NOTE: We could also handle redirects
        if (self.owner, self.repo) != (result.owner, result.repo):
            ...

        return MyEntry(self, result)


@define
class MyImpl(ABCBase):
    @t.override
    async def get_all_entries(self) -> c.Sequence[EntryInfo]:
        config = inject.instance(Config)
        input_file = config.input_file
        if input_file is None:
            input_file = INPUT_FILE

        return list(
            CsvInput[MyEntryInfo](input_file).read(lambda x: MyEntryInfo(*x))
        )


if __name__ == "__main__":
    assert isinstance(app.info.context_settings, dict)
    app.info.context_settings["obj"] = ImplClasses(
        base=MyImpl,
        entry=MyEntry,
        entry_info=MyEntryInfo,
    )

    app()
