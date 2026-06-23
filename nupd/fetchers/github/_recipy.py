import collections.abc as c
import os
import typing as t

import pydantic
from frozendict import frozendict

from nupd import utils
from nupd.fetchers import nix_prefetch_github
from nupd.helpers.recipy import ABCRecipy, NixMetaInformation

from . import _auto_fetch as auto  # pyright: ignore[reportPrivateUsage]
from ._models import GHRepository
from ._versioning import ResolvedVersion, version_by_commit


class GithubRecipy(ABCRecipy, frozen=True):
    fetched_repo: GHRepository = pydantic.Field(exclude=True)
    prefetched: nix_prefetch_github.GithubPrefetchResult = pydantic.Field(
        exclude=True
    )

    @classmethod
    async def fetch(
        cls,
        owner: str,
        repo: str,
        *,
        versioning_strategy: c.Callable[
            [GHRepository], c.Awaitable[ResolvedVersion]
        ] = version_by_commit,
        attribute_overrides: dict[str, t.Any] | None = None,
        full: bool = True,
        github_token: str | None = "auto",  # noqa: S107 # possible hardcoded password
    ) -> t.Self:
        """Fetch GitHub repository and turn it into a ``fetchFromGitHub`` call.

        Parameters:
            owner: For https://github.com/NixOS/nixpkgs, it would be ``NixOS``.
            repo: For https://github.com/NixOS/nixpkgs, it would be ``nixpkgs``.
            versioning_strategy:
                Strategy function, that turns :class:`.GHRepository` into a Nix
                formatted version (e.g. ``1.2.3-unstable-2026-06-17``).

                Valid values:
                - :func:`.version_by_tag` (``1.2.3``)
                - :func:`.version_by_commit` (``1.2.3-unstable-2026-06-17``)

                Default is :func:`.version_by_commit`.
            attribute_overrides:
                Calls :func:`utils.replace() <nupd.utils.replace>` right after
                a call to :func:`.github_fetch_auto`.
            full:
                Whether to use :func:`.github_fetch_auto` or
                :func:`.github_full_fetch_auto`.
            github_token:
                If this is ``"auto"`` (the default), the function tries to get
                the token from ``os.environ["GITHUB_TOKEN"]``.
        """
        if github_token == "auto":  # noqa: S105 # possible hardcoded password
            github_token = os.environ.get("GITHUB_TOKEN")

        if full:
            result = await auto.github_full_fetch_auto(
                owner,
                repo,
                github_token=github_token,
                attribute_overrides=attribute_overrides,
            )
        else:
            result = await auto.github_fetch_auto(
                owner, repo, github_token=github_token
            )
            if attribute_overrides:
                result = utils.replace(result, **attribute_overrides)

        version = await versioning_strategy(result)

        prefetched = await nix_prefetch_github.prefetch_github(
            result.owner,
            result.repo,
            revision=version.reference,
            fetch_submodules=bool(result.has_submodules),
            github_token=github_token,
        )

        fetcher_args: dict[str, t.Any] = {
            "owner": prefetched.owner,
            "repo": prefetched.repo,
            "hash": prefetched.hash,
        }
        if prefetched.fetch_submodules:
            fetcher_args["fetchSubmodules"] = True
        fetcher_args["rev" if version.is_commit else "tag"] = version.reference

        return cls(
            version=version.version,
            fetcher="fetchFromGitHub",
            fetcher_args=frozendict(fetcher_args),
            meta=NixMetaInformation(
                description=result.meta.description,
                homepage=result.meta.homepage,
                license=result.meta.license,
            ),
            fetched_repo=result,
            prefetched=prefetched,
        )
