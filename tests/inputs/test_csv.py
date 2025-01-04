import typing as t
from pathlib import Path

import attrs
import pytest
from attrs import define

from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo


@define(frozen=True)
class CsvEntryInfo(EntryInfo):
    name: str
    value: str

    @property
    @t.override
    def id(self) -> str:
        return self.name

    @t.override
    async def fetch(self) -> Entry[t.Any]:
        raise NotImplementedError


@pytest.fixture
def csv_input(tmp_path: Path) -> CsvInput[CsvEntryInfo]:
    return CsvInput[CsvEntryInfo](file=tmp_path / "input.csv")


def test_csv_read(csv_input: CsvInput[CsvEntryInfo]) -> None:
    with csv_input.file.open("w") as f:
        f.writelines(
            [
                "name,value\n",
                "some,thing\n",
                "example1,example2\n",
                "aaaa,bbbb\n",
            ]
        )

    assert list(csv_input.read(lambda x: CsvEntryInfo(**x))) == [
        CsvEntryInfo("some", "thing"),
        CsvEntryInfo("example1", "example2"),
        CsvEntryInfo("aaaa", "bbbb"),
    ]


def test_csv_write(csv_input: CsvInput[CsvEntryInfo]) -> None:
    csv_input.write(
        [
            CsvEntryInfo("some", "thing"),
            CsvEntryInfo("example1", "example2"),
            CsvEntryInfo("aaaa", "bbbb"),
        ],
        serialize=attrs.asdict,
    )

    with csv_input.file.open("r") as f:
        assert f.readlines() == [
            "name,value\n",
            "aaaa,bbbb\n",
            "example1,example2\n",
            "some,thing\n",
        ]
