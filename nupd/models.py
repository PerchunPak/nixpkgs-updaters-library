from __future__ import annotations

import abc
import typing as t

import attrs
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

    @staticmethod
    def info_converter(cls_: type[I]) -> t.Callable[[t.Any], I]:
        def wrapped(value: t.Any) -> I:
            if not isinstance(value, dict):
                if not isinstance(value, cls_):
                    raise TypeError(
                        "Invalid type provided for info field! "
                        f"{type(value).__name__} != {cls_.__name__}"
                    )
                return value
            return cls_(**value)

        return wrapped

    def __attrs_post_init__(self) -> None:
        fields = attrs.fields(self.__class__)
        (info_field,) = (field for field in fields if field.name == "info")
        if info_field.converter is None:
            raise TypeError(
                "You have to set converter to something like "
                "'Entry.info_converter(MyEntryInfo)' in order to be "
                "able to transform dict to Entry instance."
            )


@t.final
@define(frozen=True)
class ImplClasses:
    """Settings, passed to `app.info.context_settings["obj"] = HERE`."""

    base: type[ABCBase[t.Any, t.Any]]
    entry: type[Entry[t.Any]]
    entry_info: type[EntryInfo]
