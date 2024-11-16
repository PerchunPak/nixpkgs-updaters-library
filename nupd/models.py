import abc
from attrs import define


@define
class EntryInfo(abc.ABC):
    @abc.abstractmethod
    async def fetch(self) -> Entry:
        raise NotImplementedError


@define
class Entry:
    info: EntryInfo
