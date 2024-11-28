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
    def read(self, parse: c.Callable[[list[str]], I]) -> c.Iterable[I]:
        with self.file.open("r", newline="") as f:
            parsed = csv.reader(f, **self.kwargs)  # pyright: ignore[reportAny]

            for line in parsed:
                yield parse(line)

    @t.override
    def write(
        self,
        entries: c.Iterable[I],
        serialize: c.Callable[[I], list[str]],
        sort: c.Callable[[I], t.Any],
    ) -> None:
        with self.file.open("w", newline="") as f:
            writer = csv.writer(f, **self.kwargs)  # pyright: ignore[reportAny]
            for entry in sorted(entries, key=sort):
                writer.writerow(serialize(entry))
