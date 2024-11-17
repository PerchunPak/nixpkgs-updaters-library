from attrs import define

from nupd.base import ABCBase, Nupd
from nupd.models import Entry, EntryInfo


@define
class DumbEntry(Entry):
    hash: str


@define
class DumbEntryInfo(EntryInfo):
    name: str

    async def fetch(self) -> DumbEntry:
        return DumbEntry(self, "sha256-some/cool/hash")


class DumbBase(ABCBase):
    async def get_all_entries(self) -> list[DumbEntryInfo]:
        return [
            DumbEntryInfo("one"),
            DumbEntryInfo("two"),
            DumbEntryInfo("three"),
        ]


async def test_nupd_fetch_entries() -> None:
    nupd = Nupd()
    res = await nupd.fetch_entries(await DumbBase(nupd).get_all_entries())
