import collections.abc as c
import typing as t

from attrs import define

from nupd.base import ABCBase
from nupd.cli import app
from nupd.models import Entry, EntryInfo, ImplClasses


@define(frozen=True)
class MyEntry(Entry):
    hash: str


@define(frozen=True)
class MyEntryInfo(EntryInfo):
    @t.override
    async def fetch(self) -> MyEntry:
        return MyEntry(self, hash="sha256-test")


@t.final
@define
class MyImpl(ABCBase):
    @t.override
    async def get_all_entries(self) -> c.Sequence[EntryInfo]:
        return [MyEntryInfo()]


if __name__ == "__main__":
    assert isinstance(app.info.context_settings, dict)
    app.info.context_settings["obj"] = ImplClasses(
        base=MyImpl,
        entry=MyEntry,
        entry_info=MyEntryInfo,
    )

    app()
