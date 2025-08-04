import asyncio
import collections.abc as c
import json
import typing as t

from loguru import logger

from nupd import exc, utils
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


@utils.memory.cache
async def nurl(
    url: str,
    revision: str | None = None,
    *,
    additional_arguments: c.Iterable[str] | None = None,
    submodules: bool = False,
    fetcher: FETCHERS | None = None,
    fallback: FETCHERS | None = None,
) -> NurlResult:
    """Just a fancy wrapper around `nurl` to handle edge-cases like caching.

    Parameters:
        fetcher: A fetcher to use. List of all possible fethers can be obtained using `nurl -l`.
        fallback: The fetcher to fall back to when nurl fails to infer it from the URL.

    Raises:
        NurlError: If `nupd` return non-zero exit code or wrote something to stderr.
    """
    logger.debug(f"Running nurl on {url}")

    if additional_arguments is None:
        additional_arguments = []
    additional_arguments = list(additional_arguments)
    if "--parse" not in additional_arguments:
        additional_arguments.append("--json")

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


async def nurl_parse(
    url: str,
    revision: str | None = None,
    *,
    additional_arguments: c.Iterable[str] | None = None,
    submodules: bool = False,
    fetcher: FETCHERS | None = None,
    fallback: FETCHERS | None = None,
) -> NurlResult:
    """Wrapper around [`nurl`][nupd.fetchers.nurl.nurl] function, to also pass `--parse` argument.

    From `nurl --help`: Parse the url without fetching the hash, output in json format.

    Example:
        ```py
        >>> nurl_parse("https://github.com/NixOS/nixpkgs")
        NurlResult(args=frozendict.frozendict({'owner': 'NixOS', 'repo': 'nixpkgs'}), fetcher='fetchFromGitHub')
        ```
    """
    if additional_arguments is None:
        additional_arguments = []

    return await nurl(
        url=url,
        revision=revision,
        additional_arguments=["--parse", *additional_arguments],
        submodules=submodules,
        fetcher=fetcher,
        fallback=fallback,
    )
