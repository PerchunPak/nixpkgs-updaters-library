from __future__ import annotations

import abc
import asyncio
import json
import typing as t

import attrs
import inject
from attrs import define, field
from loguru import logger

from nupd import utils
from nupd.injections import Config
from nupd.models import Entry, EntryInfo, ImplClasses

if t.TYPE_CHECKING:
    import collections.abc as c
    from pathlib import Path


@define
class ABCBase[E: Entry[t.Any], I: EntryInfo](abc.ABC):
    nupd: Nupd
    config: Config = field(factory=lambda: inject.instance(Config))
    _default_input_file: Path = field(init=False)
    _default_output_file: Path = field(init=False)

    @_default_input_file.default  # pyright: ignore[reportUntypedFunctionDecorator,reportAttributeAccessIssue]
    def __default_input_file2(self) -> Path:  # pyright: ignore[reportUnusedFunction]
        raise NotImplementedError(
            "Please provide a default value for the input file. See example implementation"
        )

    @_default_output_file.default  # pyright: ignore[reportUntypedFunctionDecorator,reportAttributeAccessIssue]
    def __default_output_file2(self) -> Path:  # pyright: ignore[reportUnusedFunction]
        raise NotImplementedError(
            "Please provide a default value for the output file. See example implementation"
        )

    @property
    def input_file(self) -> Path:
        input_file = self.config.input_file
        if input_file is None:
            input_file = self._default_input_file

        return input_file

    @property
    def output_file(self) -> Path:
        output_file = self.config.output_file
        if output_file is None:
            output_file = self._default_output_file

        return output_file

    @abc.abstractmethod
    def init_entry(self, id: str, data: c.Mapping[str, t.Any], /) -> E: ...  # noqa: A002

    @abc.abstractmethod
    async def get_all_entries(self, /) -> c.Iterable[I]: ...

    @abc.abstractmethod
    def write_entries_info(self, entries_info: c.Iterable[I], /) -> None: ...

    @abc.abstractmethod
    def parse_entry_id(self, unparsed_argument: str, /) -> I:
        """Parse argument, that user provided as ID for an entry, to EntryInfo."""


@t.final
@define
class Nupd:
    impls: ImplClasses = field(factory=lambda: inject.instance(ImplClasses))
    impl: ABCBase[Entry[t.Any], EntryInfo] = field(init=False)

    @impl.default  # pyright: ignore[reportUntypedFunctionDecorator,reportAttributeAccessIssue]
    def _impl_default(self) -> ABCBase[Entry[t.Any], EntryInfo]:
        return self.impls.base(self)

    async def add_cmd(self, entry_ids: c.Sequence[str]) -> None:
        entries_info = {
            self.impl.parse_entry_id(entry_id) for entry_id in entry_ids
        }
        all_entries_info = set(await self.impl.get_all_entries())

        all_entries = set(self.get_all_entries_from_the_output_file())
        old_len = len(all_entries)
        all_entries.update(
            {await entry_info.fetch() for entry_info in entries_info}
        )

        self.impl.write_entries_info(entries_info.union(all_entries_info))
        self.write_entries(all_entries)

        logger.success(f"Successfully added {len(entry_ids)} entries!")
        logger.info(
            f"Changed amount of entries from {old_len} to {len(all_entries)}"
        )

    async def update_cmd(self, _entry_ids: c.Sequence[str] | None) -> None:
        raise NotImplementedError

    async def fetch_entries(
        self, entries: c.Sequence[EntryInfo]
    ) -> set[Entry[t.Any] | BaseException]:
        config = inject.instance(Config)
        limit = config.jobs

        all_results: set[Entry[t.Any] | BaseException] = set()
        for chunk in utils.chunks(entries, limit):
            results = await asyncio.gather(
                *(entry.fetch() for entry in chunk),
                return_exceptions=True,
            )

            all_results.update(set(results))

        return all_results

    def get_all_entries_from_the_output_file(self) -> c.Iterable[Entry[t.Any]]:
        if not self.impl.output_file.exists():
            return

        with self.impl.output_file.open("r") as f:
            data = json.load(f)

        for id, entry in data.items():  # noqa: A001
            yield self.impl.init_entry(id, entry)

    def write_entries(self, entries: c.Iterable[Entry[t.Any]]) -> None:
        data: dict[str, t.Any] = {}

        for entry in entries:
            data[entry.info.id] = attrs.asdict(
                entry, value_serializer=utils.json_serialize
            )
            # don't allow two sources of truth
            del data[entry.info.id]["info"]["id"]

        with self.impl.output_file.open("w") as f:
            json.dump(data, f, indent=2)
