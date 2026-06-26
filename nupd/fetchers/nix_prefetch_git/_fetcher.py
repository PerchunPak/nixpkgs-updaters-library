import asyncio
import collections.abc as c
import json
import typing as t
from datetime import datetime

from nupd import exc, utils
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

    def to_fetcher_args(self) -> dict[str, t.Any]:
        """Transform this class to a dict, that can be passed to the Nix fetcher.

        Example:
            .. code-block:: python

                print(GitPrefetchResult(...).to_fetcher_args())
                {
                    "url": "https://git.sr.ht/~sircmpwn/hare.vim",
                    "rev": "e0d38c0563224aa7b0101f64640788691f6c15b9",
                    "hash": "sha256-RuOMLGL7qzq3KXz7XfiHmuw0qJoOgx4fV8czNUQqTLM=",
                    "fetchSubmodules": True,
                }
        """  # noqa: E501 # line too long
        fetcher_args: dict[str, t.Any] = {
            "url": self.url,
            "rev": self.rev,
            "hash": self.hash,
        }

        # disable coverage, because testing these combinations would require
        # a lot of useless parametrizing
        if self.fetch_lfs:  # pragma: no cover
            fetcher_args["fetchLFS"] = True
        if self.fetch_submodules:  # pragma: no cover
            fetcher_args["fetchSubmodules"] = True
        if self.deep_clone:  # pragma: no cover
            fetcher_args["deepClone"] = True
        if self.leave_dot_git:  # pragma: no cover
            fetcher_args["leaveDotGit"] = True

        return fetcher_args


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(cache_validation_callback=utils.cache_validate_by_revision)
async def prefetch_git(
    url: str,
    *,
    revision: str | None = None,
    additional_args: c.Iterable[str] | None = None,
) -> GitPrefetchResult:
    """Wrap `nix-prefetch-git` to handle edge-cases like caching.

    Parameters:
        revision: If ``None`` (the default), tries to fetch the last commit.
        additional_args:
            Your custom additional arguments, e.g. ``--branch-name`` or
            ``--fetch-submodules``.

    Example:
        .. code-block:: python

            await prefetch_git(
                "https://github.com/PerchunPak/nixpkgs-updaters-library",
                additional_args=[
                    "--branch-name", "foo",
                    "--leave-dotGit",
                    "--fetch-submodules",
                ],
            )

        If you provide ``--branch-name foo`` as a single string, it would equal
        to ``nix-prefetch-git ... '--branch-name foo'``. It won't work, because
        ``additional_args`` is not parsed by a shell (``/bin/sh``); you have to
        manually separate each word, otherwise the script won't recognize it as
        separate words, which leads to an obscure error.

    Raises:
        GitPrefetchError:
            If ``nix-prefetch-git`` returned non-zero exit code or wrote
            something to stderr.
    """
    if additional_args is None:
        additional_args = ()

    process = await asyncio.create_subprocess_exec(
        Executable.NIX_PREFETCH_GIT,
        url,
        *((revision,) if revision else ()),
        "--quiet",
        *additional_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise GitPrefetchError(
            f"nix-prefetch-git returned exit code {process.returncode}"
            + f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        raise GitPrefetchError(
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
