import asyncio
import collections.abc as c
import datetime as dt
import json
import os
import typing as t

from loguru import logger
from pydantic import ConfigDict, alias_generators

from nupd import exc, utils
from nupd.executables import Executable
from nupd.models import NupdModel


class GithubPrefetchError(exc.NetworkError): ...


class GithubPrefetchResult(NupdModel, frozen=True):
    model_config: ConfigDict = ConfigDict(  # pyright: ignore[reportIncompatibleVariableOverride]
        alias_generator=alias_generators.to_camel,
        validate_by_name=True,
    )

    owner: str
    repo: str
    rev: str
    hash: str

    commit_date: dt.datetime | None = None

    fetch_submodules: bool = False
    leave_dot_git: bool = False
    deep_clone: bool = False

    def to_fetcher_args(self) -> dict[str, t.Any]:
        """Transform this class to a dict, that can be passed to the Nix fetcher.

        Example:
            .. code-block:: python

                print(GithubPrefetchResult(...).to_fetcher_args())
                {
                    "owner": "SnapXL",
                    "repo": "SnapX",
                    "rev": "767e54d5e70518f186cbbe51e7b6933bddbb55bd",
                    "hash": "sha256-Vy9TUsMCgx0kh8ftz3fwylOjg/DQc/53TPeivkeUuGw=",
                    "fetchSubmodules": True,
                }
        """  # noqa: E501 # line too long
        fetcher_args: dict[str, t.Any] = {
            "owner": self.owner,
            "repo": self.repo,
            "rev": self.rev,
            "hash": self.hash,
        }

        # disable coverage, because testing these combinations would require
        # a lot of useless parametrizing
        if self.fetch_submodules:  # pragma: no cover
            fetcher_args["fetchSubmodules"] = True
        if self.leave_dot_git:  # pragma: no cover
            fetcher_args["leaveDotGit"] = True
        if self.deep_clone:  # pragma: no cover
            fetcher_args["deepClone"] = True

        return fetcher_args


@utils.restore_docstring_from_memorized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=utils.cache_validate_by_revision,
)
async def prefetch_github(
    owner: str,
    repo: str,
    revision: str | None = None,
    *,
    with_meta: bool = False,
    latest_release: bool = False,
    additional_arguments: c.Iterable[str] | None = None,
    fetch_submodules: bool = False,
    leave_dot_git: bool = False,
    deep_clone: bool = False,
    github_token: str | None = None,
) -> GithubPrefetchResult:
    """Just a wrapper around ``nix-prefetch-github``.

    Parameters:
        with_meta:
            Include commit date into the result.
        latest_release:
            Fetch revision for the latest release. Still uses the ``rev``
            argument instead of ``tag``.
        fetch_submodules:
            Include git submodules in the output derivation.
        leave_dot_git:
            Include .git folder in output derivation.
        deep_clone:
            Include all of the repository history in the output derivation.

    Raises:
        GithubPrefetchError:
            If ``nix-prefetch-github`` return non-zero exit code or wrote
            something to stderr.
    """
    logger.debug(f"Running nix-prefetch-github on {owner}/{repo}")

    if additional_arguments is None:
        additional_arguments = []
    additional_arguments = list(additional_arguments)

    process = await asyncio.create_subprocess_exec(
        Executable.NIX_PREFETCH_GITHUB
        if not latest_release
        else Executable.NIX_PREFETCH_GITHUB_LATEST_RELEASE,
        owner,
        repo,
        *(("--meta",) if with_meta else ()),
        *(("--rev", revision) if revision else ()),
        *(("--fetch-submodules",) if fetch_submodules else ()),
        *(("--leave-dot-git",) if leave_dot_git else ()),
        *(("--deep-clone",) if deep_clone else ()),
        *additional_arguments,
        env={**os.environ, "GITHUB_TOKEN": github_token}
        if github_token
        else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise GithubPrefetchError(
            f"nix-prefetch-github returned exit code {process.returncode}"
            + f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        raise GithubPrefetchError(
            "nix-prefetch-github wrote something to stderr! (unexpected)"
            + f"\n{stdout=}\n{stderr=}"
        )

    result = json.loads(stdout.decode())

    if with_meta:
        return GithubPrefetchResult(
            **result["src"],
            commit_date=dt.datetime.fromisoformat(
                f"{result['meta']['commitDate']} "
                + f"{result['meta']['commitTimeOfDay']}"
            ),
        )
    return GithubPrefetchResult(**result)
