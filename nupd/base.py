from __future__ import annotations

import abc
import asyncio
import dataclasses
import json
import typing as t
from collections import defaultdict
from pathlib import Path

import inject
import rich.progress
from loguru import logger

from nupd import utils
from nupd.injections import Config
from nupd.models import Entry, EntryInfo, ImplClasses, MiniEntry

if t.TYPE_CHECKING:
    import collections.abc as c
    import os


async def _fetch_entries_worker[T](
    *,
    semaphore: asyncio.Semaphore,
    progress: rich.progress.Progress,
    task_id: rich.progress.TaskID,
    func: c.Awaitable[T],
) -> T:
    async with semaphore:
        r = await func
        progress.advance(task_id)
        return r


def undefined_default() -> t.Never:
    raise NotImplementedError(
        "Please provide a default value for the input/output file. See the"
        + "example implementation"
    )


def _entries_to_map(
    all_entries: c.Iterable[EntryInfo],
) -> c.Mapping[str, EntryInfo]:
    """Transform a list of :class:`.EntryInfo` to a map where ``{id: entry}``.

    Raises:
        ValueError: If any duplicates found.
    """
    result: dict[str, EntryInfo] = {}
    duplicates: dict[str, list[EntryInfo]] = defaultdict(list)

    for entry in all_entries:
        if entry.id in result:
            duplicates[entry.id].append(entry)
        else:
            result[entry.id] = entry

    if duplicates:
        message = ""
        for key, entries in duplicates.items():
            message += f"id={key!r}:\n"
            message += f"  {result[key]!r}\n"
            for entry in entries:
                message += f"  {entry!r}\n"

        raise ValueError(f"These entries have duplicate IDs!\n{message}")

    return result


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
        """Parse argument, that user provided as ID for the entry, to :class:`.EntryInfo`."""  # noqa: E501 # one character off...

    def gen_autocommit_message_add(self, entry: GEntry, /) -> str:  # pyright: ignore[reportUnusedParameter]
        """Generate commit message, when user adds a new entry.

        Example: ``somePlugins.{id}: init at {version}``.
        """
        raise NotImplementedError

    def gen_autocommit_message_update_one(
        self,
        # this argument is MiniEntry, but to properly support annotation
        # I would need to add another generics argument to this class.
        # And I don't want to do this right now
        old_entry: t.Any,  # pyright: ignore[reportUnusedParameter]
        entry: GEntry,  # pyright: ignore[reportUnusedParameter]
        /,
    ) -> str:
        """Generate commit message, when user updates one entry.

        Example: ``somePlugins.{id}: {old_version} -> {new_version}``.
        """
        raise NotImplementedError

    def gen_autocommit_message_update_all(self, /) -> str:
        """Generate commit message, when user updates all entries.

        Example: ``somePlugins: update on {today}``.
        """
        raise NotImplementedError

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

    @property
    def is_autocommit_implemented(self) -> bool:
        # check if all required methods were overwritten by child
        return (
            type(self.impl).gen_autocommit_message_add
            != ABCBase.gen_autocommit_message_add
            and type(self.impl).gen_autocommit_message_update_one
            != ABCBase.gen_autocommit_message_update_one
            and type(self.impl).gen_autocommit_message_update_all
            != ABCBase.gen_autocommit_message_update_all
        )

    async def add_cmd(
        self, to_add: c.Sequence[str], *, autocommit: bool = False
    ) -> None:
        if (  # pragma: no cover # tests access the property directly
            autocommit and not self.is_autocommit_implemented
        ):
            logger.error("This updater does not support --autocommit")
            return

        entries_info = {
            self.impl.parse_entry_id(entry_id) for entry_id in to_add
        }
        all_entries_info = set(await self.impl.get_all_entries())

        all_entries: dict[str, Entry[t.Any, t.Any] | MiniEntry[t.Any]] = {
            entry.info.id: entry
            for entry in self.get_all_entries_from_the_output_file()
        }
        old_len = len(all_entries)
        new_entries = await self.fetch_entries(entries_info)

        logger.success(f"Successfully fetched {len(new_entries)} entries")

        if autocommit:
            for entry in new_entries.values():
                message = self.impl.gen_autocommit_message_add(entry)
                logger.info(
                    f"Committing {entry.info.id} with message {message!r}..."
                )

                all_entries_info.add(entry.info)
                all_entries[entry.info] = entry
                self.impl.write_entries_info(all_entries_info.copy())
                self.write_entries(set(all_entries.values()))

                await utils.git_commit(message)

        else:
            all_entries.update(new_entries)
            self.impl.write_entries_info(entries_info.union(all_entries_info))
            self.write_entries(set(all_entries.values()))

        logger.success(f"Successfully added {len(to_add)} entries!")
        logger.info(
            f"Changed amount of entries from {old_len} to {len(all_entries)}"
        )

    async def update_cmd(
        self, to_update: c.Sequence[str] | None, *, autocommit: bool = False
    ) -> None:
        if (  # pragma: no cover # tests access the property directly
            autocommit and not self.is_autocommit_implemented
        ):
            logger.error("This updater does not support --autocommit")
            return

        all_entries: c.Mapping[str, Entry[t.Any, t.Any] | MiniEntry[t.Any]] = {}
        all_entries_info = _entries_to_map(await self.impl.get_all_entries())

        if not to_update:  # update all entries
            all_entries = await self.fetch_entries(all_entries_info.values())
            logger.success(f"Successfully fetched {len(all_entries)} entries")

            if autocommit:
                message = self.impl.gen_autocommit_message_update_all()
                logger.info(f"Committing with message {message!r}...")

                self.write_entries(set(all_entries.values()))
                await utils.git_commit(message)
            else:
                self.write_entries(set(all_entries.values()))

        else:  # update only selected entries
            entries_info: set[EntryInfo] = set()
            for entry_id in to_update:
                if entry_id in all_entries_info:
                    entries_info.add(all_entries_info[entry_id])
                else:
                    entries_info.add(self.impl.parse_entry_id(entry_id))

            for entry in self.get_all_entries_from_the_output_file():
                all_entries[entry.info.id] = entry

            if autocommit:
                updated_entries = await self.fetch_entries(entries_info)
                logger.success(
                    f"Successfully fetched {len(updated_entries)} entries"
                )

                for new_entry in reversed(updated_entries.values()):
                    old_entry = all_entries.pop(new_entry.info.id)
                    all_entries[new_entry.info.id] = new_entry

                    message = self.impl.gen_autocommit_message_update_one(
                        old_entry, new_entry
                    )
                    logger.info(
                        f"Committing {new_entry.info.id} "
                        + f"with message {message!r}..."
                    )

                    self.write_entries(set(all_entries.values()))
                    await utils.git_commit(message)
            else:
                all_entries.update(await self.fetch_entries(entries_info))
                self.write_entries(set(all_entries.values()))

        logger.success(
            f"Successfully updated {len(all_entries_info) or len(all_entries)} "
            + "entries!"
        )

    async def fetch_entries(
        self,
        entries: c.Collection[EntryInfo],
    ) -> dict[str, Entry[t.Any, t.Any]]:
        config = inject.instance(Config)
        logger.info(
            f"Going to fetch {len(entries)} entries with the limit of "
            + f"{config.jobs} simultaneously"
        )

        all_results: dict[str, Entry[t.Any, t.Any]] = {}
        semaphore = asyncio.Semaphore(config.jobs)
        with rich.progress.Progress(
            *utils.get_formatted_progress_bar(),
            console=utils.console,
        ) as progress:
            task_id = progress.add_task("Fetching entries", total=len(entries))
            done, pending = await asyncio.wait(
                {
                    asyncio.create_task(
                        _fetch_entries_worker(
                            semaphore=semaphore,
                            progress=progress,
                            task_id=task_id,
                            func=entry.fetch(),
                        ),
                        name=entry.id,
                    )
                    for entry in sorted(entries, key=lambda x: x.id)
                },
                return_when=asyncio.FIRST_EXCEPTION,
            )

        # TODO: this does not collect errors
        if pending:
            for task in pending:
                _ = task.cancel()

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
            data[entry.info.id] = entry.model_dump(
                mode="json", exclude_none=True
            )

        with self.impl.output_file.open("w", newline="\n") as f:
            json.dump(data, f, indent="\t", sort_keys=True)
            # add a new line on the end of the file, because nixpkgs CI
            # requires it
            _ = f.write("\n")
