from __future__ import annotations

import asyncio
import typing as t
from datetime import datetime
from pathlib import Path

import pytest
from attrs import define, field
from loguru import logger

from nupd.base import ABCBase, Nupd
from nupd.models import Entry, EntryInfo, ImplClasses

if t.TYPE_CHECKING:
    import collections.abc as c

    from pytest_mock import MockerFixture

    from tests.conftest import MOCK_INJECT


@define(frozen=True)
class DumbEntryInfo(EntryInfo):
    name: str

    @property
    @t.override
    def id(self) -> str:
        return self.name

    @t.override
    async def fetch(self) -> DumbEntry:
        logger.debug(f"Fetching {self!r}")
        return DumbEntry(self, "sha256-some/cool/hash")


@define(frozen=True)
class TimeoutEntryInfo(DumbEntryInfo):
    @t.override
    async def fetch(self) -> t.Never:
        await asyncio.sleep(10)


@define(frozen=True)
class DumbEntry(Entry[DumbEntryInfo]):
    info: DumbEntryInfo = field(
        converter=lambda x: DumbEntryInfo(**x)
        if not isinstance(x, DumbEntryInfo)
        else x
    )
    hash: str
    some_date: datetime = field(factory=lambda: datetime.fromtimestamp(0))  # noqa: DTZ006


@define
class DumbBase(ABCBase[DumbEntry, DumbEntryInfo]):
    _default_input_file: Path = Path("/homeless-shelter")
    _default_output_file: Path = Path("/homeless-shelter")

    @t.override
    async def get_all_entries(self) -> c.Sequence[DumbEntryInfo]:
        return [
            DumbEntryInfo("one"),
            DumbEntryInfo("two"),
            DumbEntryInfo("three"),
        ]

    @t.override
    def write_entries_info(
        self, _entries_info: c.Iterable[DumbEntryInfo]
    ) -> None:
        raise NotImplementedError

    @t.override
    def parse_entry_id(self, unparsed_argument: str) -> DumbEntryInfo:
        return DumbEntryInfo(unparsed_argument)


@pytest.fixture(autouse=True)
def mock_inject_impl_classes(mock_inject: MOCK_INJECT) -> None:
    mock_inject(
        ImplClasses,
        ImplClasses(
            base=DumbBase,
            entry=DumbEntry,
            entry_info=DumbEntryInfo,
        ),
    )


async def test_nupd_fetch_entries() -> None:
    res = await Nupd().fetch_entries(await DumbBase().get_all_entries())
    assert sorted(res.values(), key=lambda x: x.info.id) == [
        DumbEntry(DumbEntryInfo("one"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("three"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("two"), "sha256-some/cool/hash"),
    ]


async def test_add_cmd(mocker: MockerFixture) -> None:
    entries_info = {
        DumbEntryInfo("one"),
        DumbEntryInfo("two"),
        DumbEntryInfo("three"),
    }
    _ = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file",
        return_value=[
            DumbEntry(info, "sha256-some/cool/hash") for info in entries_info
        ],
    )
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    await Nupd().add_cmd(["four", "five"])

    new_entries_info = {
        DumbEntryInfo("four"),
        DumbEntryInfo("five"),
    }
    entries_info = entries_info.union(new_entries_info)

    spy_fetch_entries.assert_called_once()
    assert spy_fetch_entries.await_args.args[1] == new_entries_info  # pyright: ignore[reportOptionalMemberAccess]
    mocked_write_info.assert_called_once_with(entries_info)
    mocked_write_entries.assert_called_once()
    assert len(mocked_write_entries.call_args.args) == 1
    assert list(mocked_write_entries.call_args.args[0]) == [
        DumbEntry(info=DumbEntryInfo(name=name), hash="sha256-some/cool/hash")
        for name in ["two", "one", "three", "four", "five"]
    ]


async def test_update_cmd_everything(mocker: MockerFixture) -> None:
    entries_info = {
        DumbEntryInfo("one"),
        DumbEntryInfo("two"),
        DumbEntryInfo("three"),
    }
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_gaeftof = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file"
    )
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    await Nupd().update_cmd(entry_ids=None)

    spy_fetch_entries.assert_called_once()
    mocked_gaeftof.assert_not_called()
    mocked_write_info.assert_not_called()
    mocked_write_entries.assert_called_once_with(
        {DumbEntry(info, "sha256-some/cool/hash") for info in entries_info}
    )


async def test_update_cmd_specific(mocker: MockerFixture) -> None:
    entries_info = {
        DumbEntryInfo("one"),
        DumbEntryInfo("two"),
        DumbEntryInfo("three"),
    }
    _ = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file",
        return_value=[
            DumbEntry(info, "sha256-some/old/hash") for info in entries_info
        ],
    )
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    await Nupd().update_cmd(["one", "three"])

    spy_fetch_entries.assert_called_once()
    assert spy_fetch_entries.await_args.args[1] == {  # pyright: ignore[reportOptionalMemberAccess]
        DumbEntryInfo("one"),
        DumbEntryInfo("three"),
    }
    mocked_write_info.assert_not_called()
    mocked_write_entries.assert_called_once_with(
        {
            DumbEntry(DumbEntryInfo("two"), "sha256-some/old/hash"),
            DumbEntry(DumbEntryInfo("one"), "sha256-some/cool/hash"),
            DumbEntry(DumbEntryInfo("three"), "sha256-some/cool/hash"),
        }
    )


@pytest.mark.parametrize("file_exists", [True, False])
def test_get_all_entries_from_the_output_file(
    mocker: MockerFixture,
    tmp_path: Path,
    file_exists: bool,  # noqa: FBT001
) -> None:
    output_file = tmp_path / "output.json"
    _ = mocker.patch.object(DumbBase, "output_file", output_file)

    nupd = Nupd()
    entries = [
        DumbEntry(DumbEntryInfo("one"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("three"), "sha256-some/cool/hash"),
        DumbEntry(DumbEntryInfo("two"), "sha256-some/cool/hash"),
    ]

    if file_exists:
        nupd.write_entries(entries)
    assert list(nupd.get_all_entries_from_the_output_file()) == (
        entries if file_exists else []
    )
