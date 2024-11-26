from __future__ import annotations

import abc

from attrs import define


@define(frozen=True)
class EntryInfo(abc.ABC):
    """A minimal amount of information that is only enough to prefetch the entry."""

    @abc.abstractmethod
    async def fetch(self) -> Entry:
        raise NotImplementedError


@define(frozen=True)
class Entry(abc.ABC):
    """All information about the entry, that we need to generate Nix code."""

    info: EntryInfo
