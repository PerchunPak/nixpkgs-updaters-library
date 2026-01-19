from __future__ import annotations

import abc
import asyncio
import dataclasses
import json
import typing as t
from pathlib import Path

import inject
from loguru import logger

from nupd import utils
from nupd.injections import Config
from nupd.models import Entry, EntryInfo, ImplClasses, MiniEntry

if t.TYPE_CHECKING:
    import collections.abc as c
    import os


def undefined_default() -> t.Never:
    raise NotImplementedError(
        "Please provide a default value for the input/output file. See the example implementation"
    )


@dataclasses.dataclass
class ABCBase[GEntry: Entry[t.Any, t.Any], GEntryInfo: EntryInfo](abc.ABC):
    config: Config = dataclasses.field(
        default_factory=lambda: inject.instance(Config)
    )

    _default_input_file: os.PathLike[str] = dataclasses.field(
        init=False, default_factory=undefined_default
    )
    _default_output_file: os.PathLike[str] = dataclasses.field(
        init=False, default_factory=undefined_default
    )

    @property
    def input_file(self) -> Path:
        input_file = self.config.input_file
        if input_file is None:
            input_file = self.__resolve_default_path(self._default_input_file)

        return Path(input_file)

    @property
    def output_file(self) -> Path:
        output_file = self.config.output_file
        if output_file is None:
            output_file = self.__resolve_default_path(self._default_output_file)

        return Path(output_file)

    @abc.abstractmethod
    async def get_all_entries(self, /) -> c.Iterable[GEntryInfo]: ...

    @abc.abstractmethod
    def write_entries_info(
        self, entries_info: c.Iterable[GEntryInfo], /
    ) -> None: ...

    @abc.abstractmethod
    def parse_entry_id(self, unparsed_argument: str, /) -> GEntryInfo:
        """Parse argument, that user provided as an ID for the entry, to [EntryInfo](models.md#entryinfo)."""

    def __resolve_default_path(
        self, path: os.PathLike[str]
    ) -> os.PathLike[str]:
        placeholder = str(utils.NIXPKGS_PLACEHOLDER) + "/"
        if str(path).startswith(placeholder):
            return self.config.nixpkgs_path / str(path).removeprefix(
                placeholder
            )
        return path


@t.final
@dataclasses.dataclass
class Nupd:
    impls: ImplClasses = dataclasses.field(
        default_factory=lambda: inject.instance(ImplClasses)
    )
    impl: ABCBase[Entry[t.Any, t.Any], EntryInfo] = dataclasses.field(
        init=False
    )

    def __post_init__(self) -> None:
        self.impl = t.cast(
            "type[ABCBase[Entry[t.Any, t.Any], EntryInfo]]", self.impls.base
        )()

    async def add_cmd(self, entry_ids: c.Sequence[str]) -> None:
        entries_info = {
            self.impl.parse_entry_id(entry_id) for entry_id in entry_ids
        }
        all_entries_info = set(await self.impl.get_all_entries())

        all_entries: dict[str, Entry[t.Any, t.Any] | MiniEntry[t.Any]] = {
            entry.info: entry
            for entry in self.get_all_entries_from_the_output_file()
        }
        old_len = len(all_entries)
        all_entries.update(await self.fetch_entries(entries_info))

        self.impl.write_entries_info(entries_info.union(all_entries_info))
        self.write_entries(all_entries.values())

        logger.success(f"Successfully added {len(entry_ids)} entries!")
        logger.info(
            f"Changed amount of entries from {old_len} to {len(all_entries)}"
        )

    async def update_cmd(self, entry_ids: c.Sequence[str] | None) -> None:
        all_entries: c.Mapping[str, Entry[t.Any, t.Any] | MiniEntry[t.Any]] = {}
        all_entries_info = {
            info.id: info for info in await self.impl.get_all_entries()
        }

        if not entry_ids:  # update all entries
            all_entries = await self.fetch_entries(all_entries_info.values())
        else:  # update only selected entries
            entries_info: set[EntryInfo] = set()
            for entry_id in entry_ids:
                if entry_id in all_entries_info:
                    entries_info.add(all_entries_info[entry_id])
                else:
                    entries_info.add(self.impl.parse_entry_id(entry_id))

            for entry in self.get_all_entries_from_the_output_file():
                all_entries[entry.info.id] = entry

            all_entries.update(await self.fetch_entries(entries_info))

        self.write_entries(set(all_entries.values()))
        logger.success(
            f"Successfully updated {len(all_entries_info) or len(all_entries)} entries!"
        )

    async def fetch_entries(
        self,
        entries: c.Collection[EntryInfo],
    ) -> dict[str, Entry[t.Any, t.Any]]:
        config = inject.instance(Config)
        logger.info(
            f"Going to fetch {len(entries)} entries with the limit of {config.jobs}"
            " simultaneously"
        )

        all_results: dict[str, Entry[t.Any, t.Any]] = {}
        for chunk in utils.chunks(list(entries), config.jobs):
            logger.debug(f"Next chunk ({len(chunk)})")

            done, pending = await asyncio.wait(
                {
                    asyncio.create_task(entry.fetch(), name=entry.id)
                    for entry in chunk
                },
            )

            assert len(pending) == 0
            for task in done:
                all_results[task.get_name()] = task.result()

        return all_results

    def get_all_entries_from_the_output_file(
        self,
    ) -> c.Iterable[MiniEntry[t.Any]]:
        if not self.impl.output_file.exists():
            return

        with self.impl.output_file.open("r", newline="\n") as f:
            data = json.load(f)

        for entry in data.values():
            yield self.impls.mini_entry(**entry)

    def write_entries(
        self, entries: c.Iterable[Entry[t.Any, t.Any] | MiniEntry[t.Any]]
    ) -> None:
        data: dict[str, t.Any] = {}

        for entry in entries:
            if isinstance(entry, Entry):
                entry = entry.minify()  # noqa: PLW2901
            data[entry.info.id] = entry.model_dump(mode="json")

        with self.impl.output_file.open("w", newline="\n") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            # add a new line on the end of the file, because nixpkgs CI requires it
            _ = f.write("\n")
