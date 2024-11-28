import abc
import collections.abc as c
import typing as t

from nupd.models import EntryInfo


class ABCInput[I: EntryInfo](abc.ABC):
    @abc.abstractmethod
    def read(self, parse: c.Callable[..., I]) -> c.Iterable[I]: ...

    @abc.abstractmethod
    def write(
        self,
        entries: c.Iterable[I],
        serialize: c.Callable[[I], t.Any],
        sort: c.Callable[[t.Any], t.Any],
    ) -> None: ...


class ABCAsyncInput[I: EntryInfo](abc.ABC):
    @abc.abstractmethod
    async def read(self, parse: c.Callable[..., I]) -> c.Iterable[I]: ...

    @abc.abstractmethod
    async def write(
        self,
        entries: c.Iterable[I],
        serialize: c.Callable[[I], t.Any],
        sort: c.Callable[[t.Any], t.Any],
    ) -> None: ...


type ABCInputType[I: EntryInfo] = ABCInput[I] | ABCAsyncInput[I]
