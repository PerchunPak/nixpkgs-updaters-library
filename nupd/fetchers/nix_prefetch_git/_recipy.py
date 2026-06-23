import collections.abc as c
import enum
import typing as t

import pydantic
from frozendict import frozendict

from nupd.fetchers import nix_prefetch_git
from nupd.helpers import git as git_helpers
from nupd.helpers.recipy import ABCRecipy, NixMetaInformation


class GitPrefetchVersioning(enum.Enum):
    BY_COMMIT = enum.auto()
    LATEST_TAG = enum.auto()


class GitRecipy(ABCRecipy, frozen=True):
    prefetched: nix_prefetch_git.GitPrefetchResult = pydantic.Field(
        exclude=True
    )

    @classmethod
    async def fetch(
        cls,
        url: str,
        *,
        additional_args: c.Iterable[str] | None = None,
        versioning_strategy: GitPrefetchVersioning = GitPrefetchVersioning.BY_COMMIT,  # noqa: E501 # line too long
    ) -> t.Self:
        """Fetch Git repository and turn it into a ``fetchgit`` call.

        Parameters:
            url: Repository URL.
            additional_args:
                ``additional_args`` from :func:`.prefetch_git`.
            versioning_strategy:
                Which versioning strategy to use. Valid values:
                - :attr:`.GitPrefetchVersioning.LATEST_TAG` (``1.2.3``)
                - :attr:`.GitPrefetchVersioning.BY_COMMIT`
                  (``1.2.3-unstable-2026-06-17``)

                Default is :attr:`.GitPrefetchVersioning.BY_COMMIT`.
        """
        tags = await git_helpers.list_git_tags(url)
        latest_tag = git_helpers.find_latest_tag(tags)

        prefetched = await nix_prefetch_git.prefetch_git(
            url,
            revision=(
                latest_tag.reference
                if latest_tag
                and versioning_strategy == GitPrefetchVersioning.LATEST_TAG
                else None
            ),
            additional_args=additional_args,
        )
        fetcher_args = prefetched.to_fetcher_args()

        if (
            latest_tag
            and versioning_strategy == GitPrefetchVersioning.LATEST_TAG
        ):
            fetcher_args.pop("rev")
            fetcher_args["tag"] = latest_tag.reference

        return cls(
            version=_build_version(prefetched, versioning_strategy, latest_tag),
            fetcher="fetchgit",
            fetcher_args=frozendict(fetcher_args),
            meta=NixMetaInformation(),
            prefetched=prefetched,
        )


def _build_version(
    prefetched: nix_prefetch_git.GitPrefetchResult,
    versioning: GitPrefetchVersioning,
    latest_tag: git_helpers.GitTag | None,
) -> str:
    parsed = latest_tag.parsed if latest_tag else None

    if versioning == GitPrefetchVersioning.LATEST_TAG and parsed:
        return str(parsed)

    return f"{parsed or 0}-unstable-{prefetched.date.date()}"
