from __future__ import annotations

import abc
import typing as t

from attrs import define

if t.TYPE_CHECKING:
    from nupd.base import ABCBase


@define(frozen=True)
class EntryInfo(abc.ABC):
    """A minimal amount of information that is only enough to prefetch the entry."""

    @abc.abstractmethod
    async def fetch(self) -> Entry:
        raise NotImplementedError


@define
class Entry(abc.ABC):
    """All information about the entry, that we need to generate Nix code."""

    info: EntryInfo

    @abc.abstractmethod
    async def resolve(self, /) -> None:
        """Do all work so this instance is ready to be serialized to another format.

        Example would be network operations: prefetch commit, prefetch hash, etc.
        """


@t.final
@define(frozen=True)
class ImplClasses:
    """Settings, passed to `app.info.context_settings["obj"] = HERE`."""

    base: type[ABCBase]
    entry: type[Entry]
    entry_info: type[EntryInfo]
