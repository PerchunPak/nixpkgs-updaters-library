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
    """Just a fancy wrapper around `nix-prefetch-url` to handle edge-cases like caching.

    Parameters:
        unpack:
            Whether to atomatically unpack the archive (raises an error if the
            provided URL is not an archive).
        name: A custom name to give in the Nix store.

    Raises:
        URLPrefetchError: If `nix-prefetch-url` return non-zero exit code or wrote something to stderr.
    """
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
    """Convenience function for objects that implement `get_prefetch_url()`.

    This function is practically useless because of superior NURL wrapper.

    Example:
        ```py
        gh_repo = await github_fetch_rest(owner="foo", repo="bar")
        await prefetch_obj(gh_repo)
        ```

        Is equal to (`1e1356f` is an arbitrary commit)

        ```py
        await prefetch_url("https://github.com/foo/bar/archive/1e1356f.tar.gz")
        ```
        Or

        ```py
        await prefetch_url(gh_repo.get_prefetch_url())
        ```
    """
    return await prefetch_url(obj.get_prefetch_url())
