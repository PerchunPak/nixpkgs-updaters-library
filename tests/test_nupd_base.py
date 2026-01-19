from __future__ import annotations

import asyncio
import dataclasses
import typing as t
from datetime import datetime
from pathlib import Path

import pytest
from loguru import logger
from pydantic import Field

from nupd.base import ABCBase, Nupd
from nupd.models import Entry, EntryInfo, ImplClasses, MiniEntry
from nupd.utils import NIXPKGS_PLACEHOLDER

if t.TYPE_CHECKING:
    import collections.abc as c
    import os

    from pytest_mock import MockerFixture

    from tests.conftest import MOCK_INJECT


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
    some_date: datetime = Field(
        default_factory=lambda: datetime.fromtimestamp(0)  # noqa: DTZ006
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
    some_date: datetime = Field(
        default_factory=lambda: datetime.fromtimestamp(0)  # noqa: DTZ006
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
        self, _entries_info: c.Iterable[DumbEntryInfo]
    ) -> None:
        raise NotImplementedError

    @t.override
    def parse_entry_id(self, unparsed_argument: str) -> DumbEntryInfo:
        name, extra = unparsed_argument, None
        if "@" in unparsed_argument:
            name, extra = unparsed_argument.split("@")
        return DumbEntryInfo(name=name, extra=extra)


@dataclasses.dataclass
class DumbBaseWithNixpkgsPath(DumbBase):
    _default_input_file: os.PathLike[str] = NIXPKGS_PLACEHOLDER / "input.csv"
    _default_output_file: os.PathLike[str] = NIXPKGS_PLACEHOLDER / "output.csv"


@pytest.fixture(autouse=True)
def mock_inject_impl_classes(mock_inject: MOCK_INJECT) -> None:
    mock_inject(
        ImplClasses,
        ImplClasses(
            mini_entry=DumbMiniEntry,
            base=DumbBase,
            entry=DumbEntry,
            entry_info=DumbEntryInfo,
        ),
    )


async def test_nupd_fetch_entries() -> None:
    res = await Nupd().fetch_entries(await DumbBase().get_all_entries())
    assert sorted(res.values(), key=lambda x: x.info.id) == [
        DumbEntry(info=DumbEntryInfo(name="one"), hash="sha256-some/cool/hash"),
        DumbEntry(
            info=DumbEntryInfo(name="three"), hash="sha256-some/cool/hash"
        ),
        DumbEntry(info=DumbEntryInfo(name="two"), hash="sha256-some/cool/hash"),
    ]


async def test_add_cmd(mocker: MockerFixture) -> None:
    entries_info = {
        DumbEntryInfo(name="one"),
        DumbEntryInfo(name="two"),
        DumbEntryInfo(name="three"),
    }
    _ = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file",
        return_value=[
            DumbEntry(info=info, hash="sha256-some/cool/hash")
            for info in entries_info
        ],
    )
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    await Nupd().add_cmd(["four", "five"])

    new_entries_info = {
        DumbEntryInfo(name="four"),
        DumbEntryInfo(name="five"),
    }
    entries_info = entries_info.union(new_entries_info)

    spy_fetch_entries.assert_called_once()
    assert spy_fetch_entries.await_args.args[1] == new_entries_info  # pyright: ignore[reportOptionalMemberAccess]
    mocked_write_info.assert_called_once_with(entries_info)
    mocked_write_entries.assert_called_once()
    assert len(mocked_write_entries.call_args.args) == 1
    assert list(mocked_write_entries.call_args.args[0]) == [
        DumbEntry(info=DumbEntryInfo(name=name), hash="sha256-some/cool/hash")
        for name in ["two", "three", "one", "five", "four"]
    ]


async def test_update_cmd_everything(mocker: MockerFixture) -> None:
    entries_info = {
        DumbEntryInfo(name="one"),
        DumbEntryInfo(name="two"),
        DumbEntryInfo(name="three"),
    }
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_gaeftof = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file"
    )
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    await Nupd().update_cmd(to_update=None)

    spy_fetch_entries.assert_called_once()
    mocked_gaeftof.assert_not_called()
    mocked_write_info.assert_not_called()
    mocked_write_entries.assert_called_once_with(
        {
            DumbEntry(info=info, hash="sha256-some/cool/hash")
            for info in entries_info
        }
    )


async def test_update_cmd_specific(mocker: MockerFixture) -> None:
    entries_info = [
        DumbEntryInfo(name="one"),
        DumbEntryInfo(name="two", extra="extra"),
        DumbEntryInfo(name="three", extra="nice"),
        DumbEntryInfo(name="four"),
        DumbEntryInfo(name="five", extra="aaa"),
    ]
    _ = mocker.patch(
        "nupd.base.Nupd.get_all_entries_from_the_output_file",
        return_value=[
            DumbEntry(info=info, hash="sha256-some/old/hash")
            for info in entries_info
        ],
    )
    spy_fetch_entries = mocker.spy(Nupd, "fetch_entries")
    mocked_write_info = mocker.patch.object(DumbBase, "write_entries_info")
    mocked_write_entries = mocker.patch("nupd.base.Nupd.write_entries")

    nupd = Nupd()
    nupd.impl.all_entries = entries_info  # pyright: ignore[reportAttributeAccessIssue]
    await nupd.update_cmd(["one", "two@extra", "three"])

    spy_fetch_entries.assert_called_once()
    assert sorted(
        spy_fetch_entries.await_args.args[1],  # pyright: ignore[reportOptionalMemberAccess]
        key=lambda x: x.name,
    ) == [
        DumbEntryInfo(name="one"),
        DumbEntryInfo(name="three", extra="nice"),
        DumbEntryInfo(name="two", extra="extra"),
    ]
    mocked_write_info.assert_not_called()
    mocked_write_entries.assert_called_once_with(
        {
            DumbEntry(
                info=DumbEntryInfo(name="four"),
                hash="sha256-some/old/hash",
            ),
            DumbEntry(
                info=DumbEntryInfo(name="five", extra="aaa"),
                hash="sha256-some/old/hash",
            ),
            DumbEntry(
                info=DumbEntryInfo(name="two", extra="extra"),
                hash="sha256-some/cool/hash",
            ),
            DumbEntry(
                info=DumbEntryInfo(name="one"),
                hash="sha256-some/cool/hash",
            ),
            DumbEntry(
                info=DumbEntryInfo(name="three", extra="nice"),
                hash="sha256-some/cool/hash",
            ),
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
        DumbMiniEntry(
            info=DumbEntryInfo(name="one"), hash="sha256-some/cool/hash"
        ),
        DumbMiniEntry(
            info=DumbEntryInfo(name="three"), hash="sha256-some/cool/hash"
        ),
        DumbMiniEntry(
            info=DumbEntryInfo(name="two"), hash="sha256-some/old/hash"
        ),
    ]

    if file_exists:
        nupd.write_entries(entries)
    assert list(nupd.get_all_entries_from_the_output_file()) == (
        entries if file_exists else []
    )


def test_nixpkgs_placeholder_resolve() -> None:
    instance = DumbBaseWithNixpkgsPath()
    assert instance.input_file == Path("/nixpkgs/input.csv")
    assert instance.output_file == Path("/nixpkgs/output.csv")


def test_normal_path_is_untouched() -> None:
    instance = DumbBase()
    assert instance.input_file == Path("/input.csv")
    assert instance.output_file == Path("/output.csv")
