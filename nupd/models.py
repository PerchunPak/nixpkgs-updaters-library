from __future__ import annotations

import abc
import dataclasses
import typing as t

from pydantic import BaseModel

if t.TYPE_CHECKING:
    from nupd.base import ABCBase


class NupdModel(BaseModel, frozen=True, extra="forbid"): ...


class EntryInfo(NupdModel, abc.ABC, frozen=True):
    """A minimal amount of information that is only enough to prefetch the entry."""

    @property
    @abc.abstractmethod
    def id(self) -> str: ...

    @abc.abstractmethod
    async def fetch(self) -> Entry[t.Any]: ...


class Entry[I: EntryInfo](NupdModel, abc.ABC, frozen=True):
    """All information about the entry, that we need to generate Nix code."""

    info: I


@t.final
@dataclasses.dataclass(frozen=True)
class ImplClasses:
    """Settings, passed to `app.info.context_settings["obj"] = HERE`."""

    base: type[ABCBase[t.Any, t.Any]]
    entry: type[Entry[t.Any]]
    entry_info: type[EntryInfo]
