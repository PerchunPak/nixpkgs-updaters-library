import datetime as dt

import pytest

from nupd import utils
from nupd.fetchers.github import (
    Commit,
    GHRepository,
    MetaInformation,
    ResolvedVersion,
    version_by_commit,
    version_by_tag,
)

EXAMPLE_REPO = GHRepository(
    owner="neovim",
    repo="nvim-lspconfig",
    branch="master",
    commit=Commit(
        id="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        date=dt.datetime.fromisoformat("2023-06-01T18:52:58Z"),
    ),
    latest_version="v1.6.0",
    has_submodules=False,
    meta=MetaInformation(
        description="Quickstart configs for Nvim LSP",
        homepage="",
        license="Apache-2.0",
        stars=10794,
        archived=False,
        archived_at=None,
    ),
)


class TestResolvedVersion:
    @pytest.mark.parametrize(
        "commit", ["8f7df72ae", "6a5ed22255bbe10104ff9b72c55ec2e233a8e571"]
    )
    def test_is_commit_true(self, commit: str) -> None:
        assert (
            ResolvedVersion(
                version="1.2.3-unstable-2023-06-01", reference=commit
            ).is_commit
            is True
        )

    def test_is_commit_false(self) -> None:
        assert (
            ResolvedVersion(version="1.2.3", reference="v1.2.3").is_commit
            is False
        )


class TestVersionByCommit:
    async def test_with_tag(self) -> None:
        assert await version_by_commit(EXAMPLE_REPO) == ResolvedVersion(
            version="1.6.0-unstable-2023-06-01",
            reference="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        )

    async def test_without_tag(self) -> None:
        repo = utils.replace(EXAMPLE_REPO, latest_version=None)
        assert await version_by_commit(repo) == ResolvedVersion(
            version="0-unstable-2023-06-01",
            reference="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        )

    async def test_invalid_tag(self) -> None:
        repo = utils.replace(EXAMPLE_REPO, latest_version="foo")
        assert await version_by_commit(repo) == ResolvedVersion(
            version="0-unstable-2023-06-01",
            reference="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        )


class TestVersionByTag:
    async def test_with_tag(self) -> None:
        assert await version_by_tag(EXAMPLE_REPO) == ResolvedVersion(
            version="1.6.0",
            reference="v1.6.0",
        )

    async def test_without_tag(self) -> None:
        repo = utils.replace(EXAMPLE_REPO, latest_version="")
        assert await version_by_tag(repo) == ResolvedVersion(
            version="0-unstable-2023-06-01",
            reference="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        )

    async def test_invalid_tag(self) -> None:
        repo = utils.replace(EXAMPLE_REPO, latest_version="foo")
        assert await version_by_tag(repo) == ResolvedVersion(
            version="foo",
            reference="foo",
        )
