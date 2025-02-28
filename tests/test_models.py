# in the perfect world we wouldn't have any logic in our models,
# but I want to avoid dependency on cattrs by all cost for some reason...

import typing as t

import pytest
from attrs import define

from nupd.models import Entry, EntryInfo


@define(frozen=True)
class MyEntryInfo(EntryInfo):
    name: str

    @property
    @t.override
    def id(self) -> str:
        return self.name

    @t.override
    async def fetch(self) -> Entry[t.Any]:
        raise NotImplementedError


@define(frozen=True)
class InvalidMyEntry(Entry[MyEntryInfo]): ...


@define(frozen=True)
class ValidMyEntry(Entry[MyEntryInfo]):
    info: MyEntryInfo


def test_entry_post_init_invalid() -> None:
    with pytest.raises(TypeError, match="have to set converter to"):
        _ = InvalidMyEntry(MyEntryInfo(""))


@pytest.mark.parametrize("value", [MyEntryInfo("some"), {"name": "some"}])
def test_entry_post_init_valid(value: t.Any) -> None:
    assert ValidMyEntry(value) == ValidMyEntry(MyEntryInfo("some"))


def test_entry_post_init_valid_incorrect_type() -> None:
    with pytest.raises(
        TypeError,
        match=r"^Invalid type provided for info field! object != MyEntryInfo$",
    ):
        _ = ValidMyEntry(object())
