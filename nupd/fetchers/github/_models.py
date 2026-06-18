import typing as t
from datetime import datetime

import pydantic
from pydantic import BeforeValidator

from nupd import utils
from nupd.models import NupdModel

# mkdocstrings is not smart enough to resolve `t.Annotated` from a variable
# TODO: is this still true?
OptionalCleanedUpString = (
    BeforeValidator(lambda x: utils.cleanup_raw_string(x) or None),
)


class GitHubRelease(NupdModel, frozen=True):
    name: t.Annotated[str | None, OptionalCleanedUpString]
    tag_name: str
    created_at: datetime


class GitHubTag(NupdModel, frozen=True):
    name: str
    commit_sha: str


class MetaInformation(NupdModel, frozen=True):
    description: str | None
    homepage: str | None
    license: str | None
    stars: int
    archived: bool
    archived_at: datetime | None

    # sphinx does not allow turning off `typing.Annotated`, so we have to
    # register validators like this

    @pydantic.field_validator("description")
    @classmethod
    def _cleanup_raw_description(cls, value: str) -> str | None:
        return utils.cleanup_raw_string(value) or None

    @pydantic.field_validator("homepage")
    @classmethod
    def _cleanup_raw_homepage(cls, value: str) -> str | None:
        return value or None

    @pydantic.field_validator("license")
    @classmethod
    def _cleanup_raw_license(cls, value: str) -> str | None:
        return utils.cleanup_raw_string(value) or None


class Commit(NupdModel, frozen=True):
    id: str
    """SHA1 hash of the commit."""
    date: datetime


class GHRepository(NupdModel, frozen=True):
    owner: str
    repo: str
    branch: str
    meta: MetaInformation
    has_submodules: bool | None
    commit: Commit | None
    latest_version: str | None

    @property
    def url(self) -> str:
        """Simply returns ``https://github.com/{owner}/{repo}``."""
        return f"https://github.com/{self.owner}/{self.repo}"

    async def prefetch_commit(
        self, *, github_token: str | None = None
    ) -> t.Self:
        """Prefetch latest commit, if it is not yet prefetched.

        Note that the result object is immutable, which means this function has
        to do a copy and return it. You need to call this function like this:

        .. code-block:: python

            result = await result.prefetch_commit()
        """
        from ._fetchers import (  # noqa: PLC0415 # circular dependency
            github_does_have_submodules,
            github_prefetch_commit,
        )

        commit = await github_prefetch_commit(self, github_token=github_token)
        has_submodules = await github_does_have_submodules(
            self, github_token=github_token
        )
        return utils.replace(self, commit=commit, has_submodules=has_submodules)

    async def prefetch_latest_version(
        self, github_token: str | None = None
    ) -> t.Self:
        """Prefetch latest version, if it is not yet prefetched.

        First it tries to fetch the latest GitHub release, if it fails - it
        fallbacks to Git tags. If there are no tags, the returned object's
        :meth:`GHRepository.latest_version`
        stays ``None``.

        Note that the result object is immutable, which means this function has
        to do a copy and return it. You need to call this function like this:

        .. code-block:: python

            result = await result.prefetch_latest_version()
        """
        if self.latest_version:
            return self

        from ._fetchers import (  # noqa: PLC0415 # circular dependency
            fetch_latest_release,
            fetch_tags,
        )

        # First try to get the latest release
        latest_release = await fetch_latest_release(
            self.owner, self.repo, github_token=github_token
        )
        if latest_release is not None:
            return utils.replace(self, latest_version=latest_release.tag_name)

        # If no releases, try to get the latest tag
        tags = await fetch_tags(
            self.owner, self.repo, github_token=github_token
        )
        try:
            # GitHub returns tags in descending order
            latest_tag = next(iter(tags))
            return utils.replace(self, latest_version=latest_tag.name)
        except StopIteration:
            pass
        return self

    def get_prefetch_url(self) -> str:
        if self.commit is None:
            raise ValueError(
                "To get archive URL, you have to prefetch commit first"
            )
        return f"{self.url}/archive/{self.commit}.tar.gz"
