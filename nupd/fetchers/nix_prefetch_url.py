import asyncio
import typing as t

from nupd import exc
from nupd.executables import Executable
from nupd.models import NupdModel
from nupd.utils import memory


class URLPrefetchError(exc.NetworkError): ...


class URLPrefetchResult(NupdModel, frozen=True):
    hash: str
    path: str


@memory.cache
async def prefetch_url(
    url: str,
    *,
    unpack: bool = True,
    name: str | None = None,
) -> URLPrefetchResult:
    process = await asyncio.create_subprocess_exec(
        Executable.NIX_PREFETCH_URL,
        url,
        "--print-path",
        *(("--unpack",) if unpack else ()),
        *(("--name", name) if name is not None else ()),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise URLPrefetchError(
            f"nix-prefetch-url returned exit code {process.returncode}"
            f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        raise URLPrefetchError(
            "nix-prefetch-url wrote something to stderr! (unexpected)"
            f"\n{stdout=}\n{stderr=}"
        )

    hash, path = stdout.decode().strip().split("\n")  # noqa: A001
    return URLPrefetchResult(hash=hash, path=path)


class Prefetchable(t.Protocol):
    def get_prefetch_url(self, /) -> str: ...


async def prefetch_obj(obj: Prefetchable) -> URLPrefetchResult:
    return await prefetch_url(obj.get_prefetch_url())
