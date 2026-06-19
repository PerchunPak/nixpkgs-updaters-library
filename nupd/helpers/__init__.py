import typing as t

from nupd.fetchers.nurl import FETCHERS, NurlResult
from nupd.models import NupdModel
from nupd.utils import FrozenDict


class FetcherCall(NupdModel, frozen=True):
    fetcher: FETCHERS | str
    args: FrozenDict[str, t.Any]

    @t.overload
    @classmethod
    def from_(cls, obj: NurlResult, /) -> t.Self: ...

    @classmethod
    def from_(cls, obj: t.Any, /) -> t.Self:
        if isinstance(obj, NurlResult):
            return cls(fetcher=obj.fetcher, args=obj.args)

        raise NotImplementedError
