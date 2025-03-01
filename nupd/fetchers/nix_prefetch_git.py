import asyncio
import collections.abc as c
import json
from datetime import datetime

import inject
from loguru import logger

from nupd import exc
from nupd.cache import Cache
from nupd.executables import Executable
from nupd.models import NupdModel


class GitPrefetchError(exc.NetworkError): ...


class GitPrefetchResult(NupdModel, frozen=True):
    url: str
    rev: str
    date: datetime
    path: str
    hash: str
    fetch_lfs: bool
    fetch_submodules: bool
    deep_clone: bool
    leave_dot_git: bool


async def prefetch_git(
    url: str,
    *,
    revision: str | None = None,
    additional_args: c.Iterable[str] | None = None,
) -> GitPrefetchResult:
    cache = inject.instance(Cache)["nix-prefetch-git"]
    key = (
        "\0" + revision
        if revision
        else ""
        + (
            "\0".join(str(v) for v in additional_args)
            if additional_args
            else ""
        )
    )

    try:
        result = await cache.get(key)
    except KeyError:
        result = await _prefetch_git(
            url,
            revision=revision,
            additional_args=additional_args if additional_args else [],
        )

        await cache.set(key, result.model_dump(mode="json"))
        return result
    else:
        assert isinstance(result, dict)
        return GitPrefetchResult(
            url=result["url"],  # pyright: ignore[reportArgumentType]
            rev=result["rev"],  # pyright: ignore[reportArgumentType]
            date=result["date"],  # pyright: ignore[reportArgumentType]
            path=result["path"],  # pyright: ignore[reportArgumentType]
            hash=result["hash"],  # pyright: ignore[reportArgumentType]
            fetch_lfs=result["fetchLFS"],  # pyright: ignore[reportArgumentType]
            fetch_submodules=result["fetchSubmodules"],  # pyright: ignore[reportArgumentType]
            deep_clone=result["deepClone"],  # pyright: ignore[reportArgumentType]
            leave_dot_git=result["leaveDotGit"],  # pyright: ignore[reportArgumentType]
        )


async def _prefetch_git(
    url: str,
    *,
    revision: str | None,
    additional_args: c.Iterable[str],
) -> GitPrefetchResult:
    process = await asyncio.create_subprocess_exec(
        Executable.NIX_PREFETCH_GIT,
        url,
        *((revision,) if revision else ()),
        *additional_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise GitPrefetchError(
            f"nix-prefetch-git returned exit code {process.returncode}"
            f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        logger.trace(
            f"nix-prefetch-git wrote something to stderr!\n{stdout=}\n{stderr=}"
        )

    try:
        result = json.loads(stdout.decode())
    except json.JSONDecodeError as e:
        raise GitPrefetchError(
            f"nix-prefetch-git output invalid JSON\n{stdout=}\n{stderr=}"
        ) from e
    else:
        return GitPrefetchResult(
            url=result["url"],
            rev=result["rev"],
            date=result["date"],
            path=result["path"],
            hash=result["hash"],
            fetch_lfs=result["fetchLFS"],
            fetch_submodules=result["fetchSubmodules"],
            deep_clone=result["deepClone"],
            leave_dot_git=result["leaveDotGit"],
        )
