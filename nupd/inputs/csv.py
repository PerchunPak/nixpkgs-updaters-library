import collections.abc as c
import csv
import typing as t
from pathlib import Path

from attrs import define, field

from nupd.inputs.base import ABCInput
from nupd.models import EntryInfo


@define()
class CsvInput[I: EntryInfo](ABCInput[I]):
    file: Path
    kwargs: dict[str, t.Any] = field(factory=dict)
    """Kwargs, passed to `csv` functions."""

    @t.override
    def read(
        self, parse: c.Callable[[c.Iterable[str | None]], I]
    ) -> c.Iterable[I]:
        with self.file.open("r", newline="") as f:
            parsed = csv.reader(f, **self.kwargs)

            for line in parsed:
                yield parse(item if item else None for item in line)

    @t.override
    def write(
        self,
        entries: c.Iterable[I],
        serialize: c.Callable[[I], c.Iterable[str | None]],
    ) -> None:
        with self.file.open("w", newline="") as f:
            writer = csv.writer(f, **self.kwargs)
            for entry in sorted(entries, key=lambda x: x.id):
                writer.writerow(serialize(entry))
