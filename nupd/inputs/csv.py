import collections.abc as c
import csv
import dataclasses
import typing as t
from pathlib import Path

from nupd.inputs.base import ABCInput
from nupd.models import EntryInfo


@dataclasses.dataclass
class CsvInput[I: EntryInfo](ABCInput[I]):
    file: Path
    kwargs: dict[str, t.Any] = dataclasses.field(default_factory=dict)
    """Kwargs, passed to `csv` functions."""

    @t.override
    def read(
        self, parse: c.Callable[[c.Mapping[str, str]], I]
    ) -> c.Iterable[I]:
        with self.file.open("r", newline="") as f:
            parsed = csv.DictReader(f, **self.kwargs)

            for line in parsed:
                # TODO reference that item in a line can be an empty string
                # instead of a None. We don't handle it, as "not optional"
                # value would be opt-in and it is pretty annoying to handle
                # that
                yield parse(line)

    @t.override
    def write(
        self,
        entries: c.Iterable[I],
        serialize: c.Callable[[I], c.Mapping[str, str]],
    ) -> None:
        writer = None
        with self.file.open("w", newline="") as f:
            for i, entry in enumerate(sorted(entries, key=lambda x: x.id)):
                serialized = serialize(entry)
                if i == 0:
                    writer = csv.DictWriter(
                        f, fieldnames=serialized.keys(), **self.kwargs
                    )
                    writer.writeheader()
                assert writer is not None

                writer.writerow(serialized)
