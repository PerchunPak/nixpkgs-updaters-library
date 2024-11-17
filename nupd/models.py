from __future__ import annotations

import abc

from attrs import define


@define(frozen=True)
class EntryInfo(abc.ABC):
    @abc.abstractmethod
    async def fetch(self) -> Entry:
        raise NotImplementedError


@define(frozen=True)
class Entry(abc.ABC):
    info: EntryInfo
