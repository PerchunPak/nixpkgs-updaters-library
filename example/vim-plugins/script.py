from __future__ import annotations  # noqa: INP001

import os
import typing as t
from pathlib import Path

import attrs
from attrs import define, field
from loguru import logger

from nupd.base import ABCBase
from nupd.cli import app
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
class GHRepoInfo:
    owner: str
    name: str

    @classmethod
    def parse(cls, inp: str) -> t.Self:
        if not inp.startswith("https://github.com/"):
            raise ValueError(
                "At this point, automatic updater for Vim plugins supports only"
                " GitHub. Instead, please package the plugin in question manually"
            )

        inp = (
            inp.removeprefix("https://github.com/")
            .removesuffix(".git")
            .removesuffix("/")
        )
        owner, name = inp.split("/")
        return cls(owner, name)

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"


@define(frozen=True)
class MyEntryInfo(EntryInfo):
    repo: GHRepoInfo
    branch: str | None
    alias: str | None

    @property
    @t.override
    def id(self) -> str:
        if self.alias:
            return self.alias
        return self.repo.name

    @t.override
    async def fetch(self) -> Entry[t.Any]:
        logger.debug(f"Fetching from GitHub {self.repo.owner}/{self.repo.name}")
        github_token = os.environ.get("GITHUB_TOKEN")

        if github_token is not None:
            result = await github_fetch_graphql(
                self.repo.owner, self.repo.name, github_token
            )
        else:
            result = await github_fetch_rest(
                self.repo.owner, self.repo.name, github_token=None
            )

        if self.branch is not None:
            result = attrs.evolve(result, branch=self.branch, commit=None)

        # TODO: We could also handle redirects like this
        if (self.repo.owner, self.repo.name) != (result.owner, result.repo):
            ...

        result = await result.prefetch_commit(github_token=github_token)
        prefetched = await nurl.nurl(result.url, revision=result.commit)
        return MyEntry(info=self, fetched=result, nurl_result=prefetched)


@define(frozen=True)
class MyEntry(Entry[EntryInfo]):
    info: MyEntryInfo = field(converter=Entry.info_converter(MyEntryInfo))
    fetched: GHRepository
    nurl_result: nurl.NurlResult


@define
class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
    _default_input_file: Path = field(init=False, default=ROOT / "input.csv")
    _default_output_file: Path = field(init=False, default=ROOT / "output.json")

    @t.override
    async def get_all_entries(self) -> c.Iterable[MyEntryInfo]:
        def init_entry(args: c.Mapping[str, str]) -> MyEntryInfo:
            repo_url, branch, alias = (
                args["repo_url"],
                args["branch"],
                args["alias"],
            )

            if not branch:
                branch = None
            if not alias:
                alias = None

            return MyEntryInfo(GHRepoInfo.parse(repo_url), branch, alias)

        return CsvInput[MyEntryInfo](self.input_file).read(init_entry)

    @t.override
    def write_entries_info(self, entries_info: c.Iterable[MyEntryInfo]) -> None:
        CsvInput[MyEntryInfo](self.input_file).write(
            entries_info,
            serialize=attrs.asdict,
        )

    @t.override
    def parse_entry_id(self, to_parse: str) -> MyEntryInfo:
        url, branch, alias = to_parse, None, None

        if " as " in url:
            url, alias = url.split(" as ")
            alias = alias.strip()
        if "@" in url:
            url, branch = url.split("@")
            branch = branch.strip()

        return MyEntryInfo(
            repo=GHRepoInfo.parse(url.strip()),
            branch=branch,
            alias=alias,
        )


if __name__ == "__main__":
    if os.environ.get("GITHUB_TOKEN") is None:
        logger.warning(
            "Please provide GITHUB_TOKEN env variable to avoid rate limits, it"
            " is mandatory to run updates for all packages (or else you will be"
            " rate limited)"
        )

    assert isinstance(app.info.context_settings, dict)
    app.info.context_settings["obj"] = ImplClasses(
        base=MyImpl,
        entry=MyEntry,
        entry_info=MyEntryInfo,
    )

    app()
