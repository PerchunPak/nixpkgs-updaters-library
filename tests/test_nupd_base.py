import collections.abc as c
import typing as t

from attrs import define

from nupd.base import ABCBase, Nupd
from nupd.models import Entry, EntryInfo


@define
class DumbEntry(Entry):
    hash: str

    @t.override
    async def resolve(self, /) -> None: ...


@define(frozen=True)
class DumbEntryInfo(EntryInfo):
    name: str

    @t.override
    async def fetch(self) -> DumbEntry:
        return DumbEntry(self, "sha256-some/cool/hash")


@define
class DumbBase(ABCBase):
    @t.override
    async def get_all_entries(self) -> c.Sequence[DumbEntryInfo]:
        return [
            DumbEntryInfo("one"),
            DumbEntryInfo("two"),
            DumbEntryInfo("three"),
        ]


async def test_nupd_fetch_entries() -> None:
    nupd = Nupd()
    res = await nupd.fetch_entries(await DumbBase(nupd).get_all_entries())
    assert sorted(res, key=lambda x: x.info.name) == [  # pyright: ignore[reportAttributeAccessIssue, reportUnknownLambdaType]
        DumbEntry(DumbEntryInfo("one"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("three"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("two"), "sha256-some/cool/hash"),
    ]
