from __future__ import annotations

import asyncio
import dataclasses
import datetime as dt
import typing as t
from pathlib import Path

from loguru import logger
from pydantic import Field

from nupd.base import ABCBase
from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo, MiniEntry
from nupd.utils import NIXPKGS_PLACEHOLDER

if t.TYPE_CHECKING:
    import collections.abc as c
    import os


class DumbEntryInfo(EntryInfo, frozen=True):
    name: str
    extra: str | None = None

    @property
    @t.override
    def id(self) -> str:
        return self.name

    @t.override
    async def fetch(self) -> DumbEntry:
        logger.debug(f"Fetching {self!r}")
        return DumbEntry(info=self, hash="sha256-some/cool/hash")


class TimeoutEntryInfo(DumbEntryInfo, frozen=True):
    @t.override
    async def fetch(self) -> t.Never:
        await asyncio.sleep(10)
        raise NotImplementedError


class DumbEntry(Entry[DumbEntryInfo, t.Any], frozen=True):
    info: DumbEntryInfo
    hash: str
    some_date: dt.datetime = Field(
        default_factory=lambda: dt.datetime.fromtimestamp(0, dt.UTC)
    )

    @t.override
    def minify(self) -> DumbMiniEntry:
        return DumbMiniEntry(
            info=self.info,
            hash=self.hash,
            some_date=self.some_date,
        )


class DumbMiniEntry(MiniEntry[DumbEntryInfo], frozen=True):
    info: DumbEntryInfo
    hash: str
    some_date: dt.datetime = Field(
        default_factory=lambda: dt.datetime.fromtimestamp(0, dt.UTC)
    )


@dataclasses.dataclass
class DumbBase(ABCBase[DumbEntry, DumbEntryInfo]):
    _default_input_file: os.PathLike[str] = Path("/input.csv")
    _default_output_file: os.PathLike[str] = Path("/output.csv")

    all_entries: list[DumbEntryInfo] = dataclasses.field(
        default_factory=lambda: [
            DumbEntryInfo(name="one"),
            DumbEntryInfo(name="two"),
            DumbEntryInfo(name="three"),
        ]
    )

    @t.override
    async def get_all_entries(self) -> c.Sequence[DumbEntryInfo]:
        return self.all_entries

    @t.override
    def write_entries_info(
        self, entries_info: c.Iterable[DumbEntryInfo]
    ) -> None:
        CsvInput[DumbEntryInfo](self.input_file).write(
            entries_info,
            serialize=lambda x: x.model_dump(mode="json"),
        )

    @t.override
    def parse_entry_id(self, unparsed_argument: str) -> DumbEntryInfo:
        name, extra = unparsed_argument, None
        if "@" in unparsed_argument:
            name, extra = unparsed_argument.split("@")
        return DumbEntryInfo(name=name, extra=extra)


@dataclasses.dataclass
class DumbBaseAutocommit(DumbBase):
    @t.override
    def gen_autocommit_message_add(self, entry: DumbEntry, /) -> str:
        return f"example.{entry.info.id}: init"

    @t.override
    def gen_autocommit_message_update_one(
        self, old: DumbMiniEntry, new: DumbEntry, /
    ) -> str:
        return f"example.{new.info.id}: update"

    @t.override
    def gen_autocommit_message_update_all(self) -> str:
        return "example: update all"


@dataclasses.dataclass
class DumbBaseWithNixpkgsPath(DumbBase):
    _default_input_file: os.PathLike[str] = NIXPKGS_PLACEHOLDER / "input.csv"
    _default_output_file: os.PathLike[str] = NIXPKGS_PLACEHOLDER / "output.csv"
