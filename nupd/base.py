from __future__ import annotations

import abc
import asyncio

import inject
from attrs import define

from nupd import utils
from nupd.injections import Config
from nupd.models import Entry, EntryInfo


@define
class ABCBase(abc.ABC):
    nupd: Nupd

    async def get_all_entries(self) -> list[EntryInfo]: ...


class Nupd:
    @inject.autoparams("config")
    async def fetch_entries(
        self, entries: list[EntryInfo], config: Config
    ) -> set[Entry | Exception]:
        limit = config.jobs

        all_results: set[Entry | Exception] = set()
        for chunk in utils.chunks(entries, limit):
            results = await asyncio.gather(
                *(entry.fetch() for entry in chunk),
                return_exceptions=True,
            )

            all_results.update(set(results))

        return all_results
