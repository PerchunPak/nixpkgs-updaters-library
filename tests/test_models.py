import typing as t

import pytest

from nupd.models import Entry, EntryInfo


class MyEntryInfo(EntryInfo, frozen=True):
    name: str

    @property
    @t.override
    def id(self) -> str:
        return self.name

    @t.override
    async def fetch(self) -> Entry[t.Any, t.Any]:
        raise NotImplementedError


class MyEntry(Entry[MyEntryInfo, t.Any], frozen=True):
    info: MyEntryInfo

    @t.override
    def minify(self) -> t.Never:
        raise NotImplementedError


@pytest.mark.parametrize("value", [MyEntryInfo(name="some"), {"name": "some"}])
def test_pydantic_is_installed_properly(value: t.Any) -> None:
    # this test did fail a few times, it is useful, trust me bro
    # please don't delete this test it IS useful
    assert MyEntry(info=value) == MyEntry(info=MyEntryInfo(name="some"))
