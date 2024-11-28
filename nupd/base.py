from __future__ import annotations

import abc
import asyncio
import collections.abc as c
import typing as t

import inject
from attrs import define

from nupd import utils
from nupd.injections import Config
from nupd.models import Entry, EntryInfo


@define
class ABCBase(abc.ABC):
    nupd: Nupd

    @abc.abstractmethod
    async def get_all_entries(self) -> c.Sequence[EntryInfo]: ...


@t.final
class Nupd:
    async def fetch_entries(
        self, entries: c.Sequence[EntryInfo]
    ) -> set[Entry | BaseException]:
        config = inject.instance(Config)
        limit = config.jobs

        all_results: set[Entry | BaseException] = set()
        for chunk in utils.chunks(entries, limit):
            results = await asyncio.gather(
                *(entry.fetch() for entry in chunk),
                return_exceptions=True,
            )

            all_results.update(set(results))

        return all_results
