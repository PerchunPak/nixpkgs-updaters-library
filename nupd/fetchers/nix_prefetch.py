import asyncio

import inject
from attrs import asdict, define

from nupd import exc
from nupd.cache import Cache


class URLPrefetchError(exc.NetworkError): ...


@define(frozen=True)
class URLPrefetchResult:
    hash: str
    path: str


async def prefetch_url(
    url: str,
    *,
    unpack: bool = True,
    name: str | None = None,
) -> URLPrefetchResult:
    cache = inject.instance(Cache)["nix-prefetch"]
    key = f"{url}?name={name}&unpack={unpack}"
    try:
        result = await cache.get(key)
    except KeyError:
        try:
            result = await _prefetch_url(url, unpack=unpack, name=name)
        except URLPrefetchError as e:
            await cache.set(key, {"error": True, "msg": e.args[0]})
            raise

        await cache.set(key, asdict(result))
        return result
    else:
        assert isinstance(result, dict)
        if result.get("error", False):
            raise URLPrefetchError(result.get("msg", ""))
        return URLPrefetchResult(**result)  # pyright: ignore[reportArgumentType]


async def _prefetch_url(
    url: str,
    *,
    unpack: bool = True,
    name: str | None = None,
) -> URLPrefetchResult:
    process = await asyncio.create_subprocess_exec(
        "nix-prefetch-url",
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
