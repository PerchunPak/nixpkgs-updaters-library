from __future__ import annotations

import abc
import dataclasses
import typing as t

from pydantic import BaseModel

if t.TYPE_CHECKING:
    from nupd.base import ABCBase


class NupdModel(BaseModel, frozen=True, extra="forbid"):
    """Base class for all nupd models."""


class EntryInfo(NupdModel, abc.ABC, frozen=True):
    """Minimal amount of information that is only enough to prefetch the entry."""  # noqa: E501

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Valid Nix key by which plugin then will be referenced.

        Note that this must be a property, so you can implement (for example)
        aliases.
        """

    @abc.abstractmethod
    async def fetch(self) -> Entry[t.Any, t.Any]:
        """Fetch all the information required for the :class:`.Entry`."""


class Entry[GEntryInfo: EntryInfo, GMiniEntry: MiniEntry[t.Any]](
    NupdModel, abc.ABC, frozen=True
):
    """Fully fetched entry."""

    info: GEntryInfo

    @abc.abstractmethod
    def minify(self) -> GMiniEntry:
        """Minify all information about the entry to :class:`MiniEntry`."""


class MiniEntry[GEntryInfo: EntryInfo](NupdModel, abc.ABC, frozen=True):
    """Minified prefetched entry with the minimal set of the require keys.

    This exists with a goal to not bloat your output file with unused
    information. However, it still must have enough information to reconstruct
    an :class:`EntryInfo` instance (there is an ``info`` field for this).
    """

    info: GEntryInfo


@t.final
@dataclasses.dataclass(frozen=True)
class ImplClasses:
    """Settings, passed to `register_implementation_classes`."""

    base: type[ABCBase[t.Any, t.Any]]
    mini_entry: type[MiniEntry[t.Any]]
    entry: type[Entry[t.Any, t.Any]]
    entry_info: type[EntryInfo]
