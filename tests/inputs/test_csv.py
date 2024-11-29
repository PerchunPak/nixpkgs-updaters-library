import typing as t
from pathlib import Path

import pytest
from attrs import define

from nupd.inputs.csv import CsvInput
from nupd.models import Entry, EntryInfo


@define(frozen=True)
class CsvEntryInfo(EntryInfo):
    name: str
    value: str

    @t.override
    async def fetch(self) -> Entry:
        raise NotImplementedError


@pytest.fixture
def csv_input(tmp_path: Path) -> CsvInput[CsvEntryInfo]:
    return CsvInput[CsvEntryInfo](file=tmp_path / "input.csv")


def test_csv_read(csv_input: CsvInput[CsvEntryInfo]) -> None:
    with csv_input.file.open("w") as f:
        f.writelines(
            [
                "name,value\n",
                "example1,example2\n",
                "aaaa,bbbb\n",
            ]
        )

    assert list(csv_input.read(lambda x: CsvEntryInfo(*x))) == [
        CsvEntryInfo("name", "value"),
        CsvEntryInfo("example1", "example2"),
        CsvEntryInfo("aaaa", "bbbb"),
    ]


def test_csv_write(csv_input: CsvInput[CsvEntryInfo]) -> None:
    csv_input.write(
        [
            CsvEntryInfo("name", "value"),
            CsvEntryInfo("example1", "example2"),
            CsvEntryInfo("aaaa", "bbbb"),
        ],
        serialize=lambda x: [x.name, x.value],
        sort=lambda x: 0,
    )

    with csv_input.file.open("r") as f:
        assert f.readlines() == [
            "name,value\n",
            "example1,example2\n",
            "aaaa,bbbb\n",
        ]
