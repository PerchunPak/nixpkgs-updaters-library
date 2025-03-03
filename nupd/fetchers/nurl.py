import asyncio
import collections.abc as c
import functools
import json
import typing as t

import inject
from loguru import logger

from nupd import exc
from nupd.cache import Cache
from nupd.executables import Executable
from nupd.models import NupdModel
from nupd.utils import FrozenDict

type FETCHERS = t.Literal[
    "builtins.fetchGit",
    "fetchCrate",
    "fetchFromBitbucket",
    "fetchFromGitHub",
    "fetchFromGitLab",
    "fetchFromGitea",
    "fetchFromGitiles",
    "fetchFromRepoOrCz",
    "fetchFromSourcehut",
    "fetchHex",
    "fetchPypi",
    "fetchgit",
    "fetchhg",
    "fetchsvn",
]


class NurlError(exc.NetworkError): ...


class NurlResult(NupdModel, frozen=True):
    args: FrozenDict[str, t.Any]
    fetcher: FETCHERS


async def _cache_nurl_call[**P](
    __key_suffix: str,  # noqa: PYI063
    __implementation: c.Callable[P, c.Awaitable[NurlResult]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> NurlResult:
    cache = inject.instance(Cache)["nurl" + __key_suffix]
    key = (
        "\0".join(str(v) for v in args)
        + "\0"
        + "\0".join(f"{k}={v}" for k, v in kwargs.items())
    )

    try:
        result = await cache.get(key)
    except KeyError:
        result = await __implementation(*args, **kwargs)
        await cache.set(key, result.model_dump(mode="json"))
        return result
    else:
        assert isinstance(result, dict)
        return NurlResult(**result)  # pyright: ignore[reportArgumentType]


async def _nurl_implementation(
    url: str,
    revision: str | None = None,
    *,
    additional_arguments: c.Iterable[str] | None = None,
    submodules: bool = False,
    fetcher: FETCHERS | None = None,
    fallback: FETCHERS | None = None,
) -> NurlResult:
    logger.debug(f"Running nurl on {url}")
    if additional_arguments is None:
        additional_arguments = []

    process = await asyncio.create_subprocess_exec(
        Executable.NURL,
        url,
        *((revision,) if revision else ()),
        *(("--submodules=true",) if submodules else ()),
        *(("--fetcher", fetcher) if fetcher is not None else ()),
        *(("--fallback", fallback) if fallback is not None else ()),
        *additional_arguments,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise NurlError(
            f"nurl returned exit code {process.returncode}"
            f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        logger.trace(f"nurl wrote something to stderr!\n{stdout=}\n{stderr=}")

    return NurlResult(**json.loads(stdout.decode()))


@functools.wraps(_nurl_implementation)
async def nurl(*args: t.Any, **kwargs: t.Any) -> NurlResult:
    @functools.wraps(_nurl_implementation)
    def implementation(
        *args: t.Any,
        additional_arguments: c.Iterable[str] | None = None,
        **kwargs: t.Any,
    ) -> c.Coroutine[t.Any, t.Any, NurlResult]:
        additional_arguments = (
            list(additional_arguments)
            if additional_arguments is not None
            else []
        )
        additional_arguments.append("-j")

        return _nurl_implementation(
            *args, additional_arguments=additional_arguments, **kwargs
        )

    return await _cache_nurl_call(
        "",  # key suffix
        implementation,
        *args,
        **kwargs,
    )


@functools.wraps(_nurl_implementation)
async def nurl_parse(*args: t.Any, **kwargs: t.Any) -> NurlResult:
    @functools.wraps(_nurl_implementation)
    def implementation(
        *args: t.Any,
        additional_arguments: c.Iterable[str] | None = None,
        **kwargs: t.Any,
    ) -> c.Coroutine[t.Any, t.Any, NurlResult]:
        additional_arguments = (
            list(additional_arguments)
            if additional_arguments is not None
            else []
        )
        additional_arguments.append("-p")

        return _nurl_implementation(
            *args, additional_arguments=additional_arguments, **kwargs
        )

    return await _cache_nurl_call(
        "-parse",  # key suffix
        implementation,
        *args,
        **kwargs,
    )
