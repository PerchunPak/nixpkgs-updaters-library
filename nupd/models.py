from __future__ import annotations

import abc
import typing as t

from attrs import define

if t.TYPE_CHECKING:
    from nupd.base import ABCBase


@define(frozen=True)
class EntryInfo(abc.ABC):
    """A minimal amount of information that is only enough to prefetch the entry."""

    @property
    @abc.abstractmethod
    def id(self) -> str: ...

    @abc.abstractmethod
    async def fetch(self) -> Entry[t.Any]: ...


@define(frozen=True)
class Entry[I: EntryInfo](abc.ABC):
    """All information about the entry, that we need to generate Nix code."""

    info: I


@t.final
@define(frozen=True)
class ImplClasses:
    """Settings, passed to `app.info.context_settings["obj"] = HERE`."""

    base: type[ABCBase[t.Any, t.Any]]
    entry: type[Entry[t.Any]]
    entry_info: type[EntryInfo]
