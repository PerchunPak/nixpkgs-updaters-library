from __future__ import annotations

import collections.abc as c
import dataclasses
import os
import typing as t
from pathlib import Path

from loguru import logger

from nupd.base import ABCBase
from nupd.cli import app
from nupd.exc import InvalidArgumentError
from nupd.fetchers.github import GithubRecipy
from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo, ImplClasses
from nupd.utils import register_implementation_classes

ROOT = Path(__file__).parent.resolve()
if "/nix/store" in str(ROOT):
    # we are bundled using nix, use working directory instead of root
    ROOT = Path.cwd()  # pyright: ignore[reportConstantRedefinition]


class MyEntryInfo(EntryInfo, frozen=True):
    owner: str
    repo: str

    # This is a property because we could, for example, implement aliases
    @property
    @t.override
    def id(self) -> str:
        return self.repo


# to keep this example simple, we intentionally do not implement `MiniEntry`,
# so instead of our implementation we can just provide `Any` as a type argument.
# you can also provide `MiniEntry` if you don't want to use `Any`
class MyEntry(Entry[EntryInfo, t.Any], frozen=True):
    info: MyEntryInfo
    fetched: GithubRecipy


@dataclasses.dataclass
class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
    _default_input_file: os.PathLike[str] = dataclasses.field(
        init=False, default=ROOT / "input.csv"
    )
    _default_output_file: os.PathLike[str] = dataclasses.field(
        init=False, default=ROOT / "output.json"
    )

    @t.override
    async def get_all_entries(self) -> c.Iterable[MyEntryInfo]:
        return CsvInput[MyEntryInfo](self.input_file).read(
            lambda x: MyEntryInfo(**x)
        )

    # TODO: update docs
    @t.override
    async def fetch_entry(self, entry_info: MyEntryInfo) -> MyEntry:
        logger.debug(f"Fetching {entry_info.owner}/{entry_info.repo}")

        # fetch all possible information about the entry
        # this will also automatically use GitHub token from the `GITHUB_TOKEN`
        # environment variable
        result = await GithubRecipy.fetch(entry_info.owner, entry_info.repo)

        return MyEntry(info=entry_info, fetched=result)

    @t.override
    def write_entries_info(self, entries_info: c.Iterable[MyEntryInfo]) -> None:
        CsvInput[MyEntryInfo](self.input_file).write(
            entries_info,
            serialize=lambda x: x.model_dump(mode="json"),
        )

    @t.override
    def parse_entry_id(self, to_parse: str) -> MyEntryInfo:
        split = to_parse.split("/")
        if len(split) != 2:
            raise InvalidArgumentError(
                f"Invalid value passed: {to_parse!r}. "
                + "Should be something like 'owner/repo'"
            )

        owner, repo = split
        return MyEntryInfo(owner=owner, repo=repo)


if __name__ == "__main__":
    # this is how we point out which implementation classes we use
    register_implementation_classes(
        ImplClasses(
            base=MyImpl,
            entry=MyEntry,
            entry_info=MyEntryInfo,
        )
    )

    app.meta()
