from __future__ import annotations  # noqa: INP001

import os
import typing as t
from pathlib import Path

import attrs
from attrs import define, field
from loguru import logger

from nupd.base import ABCBase
from nupd.cli import app
from nupd.exc import InvalidArgumentError
from nupd.fetchers import nurl
from nupd.fetchers.github import (
    GHRepository,
    github_fetch_graphql,
    github_fetch_rest,
)
from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo, ImplClasses

if t.TYPE_CHECKING:
    import collections.abc as c

ROOT = Path(__file__).parent


@define(frozen=True)
class MyEntryInfo(EntryInfo):
    owner: str
    repo: str

    @property
    @t.override
    def id(self) -> str:
        # This is a property, because we could implement e.g. aliases
        return self.repo

    @t.override
    async def fetch(self) -> MyEntry:
        logger.debug(f"Fetching {self.owner}/{self.repo}")
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token is not None:
            result = await github_fetch_graphql(
                self.owner, self.repo, github_token
            )
        else:
            result = await github_fetch_rest(
                self.owner, self.repo, github_token=None
            )

        # NOTE: We could also handle redirects like this
        if (self.owner, self.repo) != (result.owner, result.repo):
            ...

        result = await result.prefetch_commit()
        prefetched = await nurl.nurl(result.url)
        return MyEntry(info=self, fetched=result, nurl_result=prefetched)


@define(frozen=True)
class MyEntry(Entry[EntryInfo]):
    fetched: GHRepository
    info: MyEntryInfo = field(converter=Entry.info_converter(MyEntryInfo))
    nurl_result: nurl.NurlResult


@define
class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
    _default_input_file: Path = field(init=False, default=ROOT / "input.csv")
    _default_output_file: Path = field(init=False, default=ROOT / "output.json")

    @t.override
    async def get_all_entries(self) -> c.Iterable[MyEntryInfo]:
        return CsvInput[MyEntryInfo](self.input_file).read(
            lambda x: MyEntryInfo(*x)
        )

    @t.override
    def write_entries_info(self, entries_info: c.Iterable[MyEntryInfo]) -> None:
        CsvInput[MyEntryInfo](self.input_file).write(
            entries_info,
            serialize=attrs.asdict,
        )

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


if __name__ == "__main__":
    assert isinstance(app.info.context_settings, dict)
    app.info.context_settings["obj"] = ImplClasses(
        base=MyImpl,
        entry=MyEntry,
        entry_info=MyEntryInfo,
    )

    app()
