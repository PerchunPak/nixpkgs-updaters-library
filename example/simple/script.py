from __future__ import annotations

import dataclasses
import typing as t
from pathlib import Path

from loguru import logger

from nupd.base import ABCBase
from nupd.cli import app
from nupd.exc import InvalidArgumentError
from nupd.fetchers.github import GithubRecipy
from nupd.helpers.recipy import (
    NixMetaInformation,  # noqa: TC001 # pydantic needs this type during runtime
)
from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo, ImplClasses, MiniEntry
from nupd.utils import FrozenDict, register_implementation_classes

if t.TYPE_CHECKING:
    import collections.abc as c
    import os


ROOT = Path(__file__).parent.resolve()
if "/nix/store" in str(ROOT):
    # we are bundled using nix, use working directory instead of root
    ROOT = Path.cwd()  # pyright: ignore[reportConstantRedefinition]


class MyEntryInfo(EntryInfo, frozen=True):
    owner: str
    repo: str

    # This is a property because we could, for example, implement aliases.
    @property
    @t.override
    def id(self) -> str:
        return self.repo

    @t.override
    async def fetch(self) -> MyEntry:
        logger.debug(f"Fetching {self.owner}/{self.repo}")

        # fetch all possible information about the entry
        # this will also automatically use GitHub token from the `GITHUB_TOKEN`
        # environment variable
        result = await GithubRecipy.fetch(self.owner, self.repo)

        # NOTE: We could also handle redirects like this
        if (self.owner, self.repo) != (
            result.fetched_repo.owner,
            result.fetched_repo.repo,
        ):
            ...

        return MyEntry(info=self, fetched=result)


class MyMiniEntry(MiniEntry[MyEntryInfo], frozen=True):
    version: str
    fetcher: str
    fetcher_args: FrozenDict[str, t.Any]
    meta: NixMetaInformation | None


class MyEntry(Entry[EntryInfo, MyMiniEntry], frozen=True):
    info: MyEntryInfo
    fetched: GithubRecipy

    @t.override
    def minify(self) -> MyMiniEntry:
        return MyMiniEntry(
            info=self.info,
            version=self.fetched.version,
            fetcher=self.fetched.fetcher,
            fetcher_args=self.fetched.fetcher_args,
            meta=self.fetched.meta,
        )


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
            mini_entry=MyMiniEntry,
            entry=MyEntry,
            entry_info=MyEntryInfo,
        )
    )

    app.meta()
