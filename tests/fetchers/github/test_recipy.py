import datetime as dt
import typing as t

import pytest
from frozendict import frozendict
from pytest_mock import MockerFixture

from nupd import utils
from nupd.fetchers.github import (
    Commit,
    GHRepository,
    GithubRecipy,
    MetaInformation as GHMetaInformation,
    version_by_commit,
    version_by_tag,
)
from nupd.fetchers.nix_prefetch_github import GithubPrefetchResult
from nupd.helpers.recipy import NixMetaInformation

COMMIT_SHA = "6a5ed22255bbe10104ff9b72c55ec2e233a8e571"
EXAMPLE_REPO = GHRepository(
    owner="neovim",
    repo="nvim-lspconfig",
    branch="master",
    commit=Commit(
        id=COMMIT_SHA,
        date=dt.datetime.fromisoformat("2023-06-01T18:52:58Z"),
    ),
    latest_version="v1.6.0",
    has_submodules=False,
    meta=GHMetaInformation(
        description="Quickstart configs for Nvim LSP",
        homepage="",
        license="Apache-2.0",
        stars=10794,
        archived=False,
        archived_at=None,
    ),
)

EXAMPLE_PREFETCH = GithubPrefetchResult(
    owner="neovim",
    repo="nvim-lspconfig",
    rev=COMMIT_SHA,
    hash="sha256-Vy9TUsMCgx0kh8ftz3fwylOjg/DQc/53TPeivkeUuGw=",
)


@pytest.mark.parametrize("fetch_submodules", [True, False])
@pytest.mark.parametrize("full", [True, False])
@pytest.mark.parametrize(
    ("version", "is_commit"),
    [
        ("1.6.0", False),
        ("1.6.0-unstable-2023-06-01", True),
    ],
)
async def test_github_recipy_fetch(
    mocker: MockerFixture,
    fetch_submodules: bool,
    full: bool,
    version: str,
    is_commit: bool,
) -> None:
    # response objects
    repo = utils.replace(EXAMPLE_REPO, has_submodules=fetch_submodules)
    prefetched = utils.replace(
        EXAMPLE_PREFETCH, fetch_submodules=fetch_submodules
    )

    # mocks
    fetch_auto = mocker.patch(
        "nupd.fetchers.github._auto_fetch.github_fetch_auto",
        mocker.async_stub(),
    )
    fetch_auto.return_value = repo
    full_fetch_auto = mocker.patch(
        "nupd.fetchers.github._auto_fetch.github_full_fetch_auto",
        mocker.async_stub(),
    )
    full_fetch_auto.return_value = repo
    prefetch_github = mocker.patch(
        "nupd.fetchers.nix_prefetch_github.prefetch_github",
        mocker.async_stub(),
    )
    prefetch_github.return_value = prefetched

    # fetcher arguments
    fetcher_args: dict[str, t.Any] = {
        "owner": prefetch_github.return_value.owner,
        "repo": prefetch_github.return_value.repo,
        "hash": prefetch_github.return_value.hash,
    }
    if fetch_submodules:
        fetcher_args["fetchSubmodules"] = True
    fetcher_args["rev" if is_commit else "tag"] = (
        COMMIT_SHA if is_commit else f"v{version}"
    )

    # assertions
    assert await GithubRecipy.fetch(
        "neovim",
        "nvim-lspconfig",
        versioning_strategy=version_by_commit if is_commit else version_by_tag,
        full=full,
        github_token="aaa",
    ) == GithubRecipy(
        version=version,
        fetcher="fetchFromGitHub",
        fetcher_args=frozendict(fetcher_args),
        meta=NixMetaInformation(
            description="Quickstart configs for Nvim LSP",
            homepage="https://github.com/neovim/nvim-lspconfig",
            license="Apache-2.0",
        ),
        fetched_repo=repo,
        prefetched=prefetched,
    )

    if full:
        fetch_auto.assert_not_called()
        _ = full_fetch_auto.assert_awaited_once_with(
            "neovim",
            "nvim-lspconfig",
            github_token="aaa",
            attribute_overrides=None,
        )
    else:
        _ = fetch_auto.assert_awaited_once_with(
            "neovim", "nvim-lspconfig", github_token="aaa"
        )
        full_fetch_auto.assert_not_called()

    _ = prefetch_github.assert_awaited_once_with(
        "neovim",
        "nvim-lspconfig",
        reference=COMMIT_SHA if is_commit else f"v{version}",
        fetch_submodules=fetch_submodules,
        github_token="aaa",
    )


@pytest.mark.parametrize("github_token", ["auto", None])
async def test_github_recipy_fetch_misc(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    github_token: str | None,
) -> None:
    # mocks
    expected_token = "aaa" if github_token == "auto" else None  # noqa: S105 # hardcoded password
    if expected_token:
        monkeypatch.setenv("GITHUB_TOKEN", expected_token)
    fetch_auto = mocker.patch(
        "nupd.fetchers.github._auto_fetch.github_fetch_auto",
        mocker.async_stub(),
    )
    fetch_auto.return_value = EXAMPLE_REPO
    prefetch_github = mocker.patch(
        "nupd.fetchers.nix_prefetch_github.prefetch_github",
        mocker.async_stub(),
    )
    prefetch_github.return_value = EXAMPLE_PREFETCH

    # fetcher arguments
    fetcher_args: dict[str, t.Any] = {
        "owner": prefetch_github.return_value.owner,
        "repo": prefetch_github.return_value.repo,
        "hash": prefetch_github.return_value.hash,
        "rev": COMMIT_SHA,
    }

    # assertions
    assert await GithubRecipy.fetch(
        "neovim",
        "nvim-lspconfig",
        versioning_strategy=version_by_commit,
        attribute_overrides={"has_submodules": True},
        full=False,
        github_token=github_token,
    ) == GithubRecipy(
        version="1.6.0-unstable-2023-06-01",
        fetcher="fetchFromGitHub",
        fetcher_args=frozendict(fetcher_args),
        meta=NixMetaInformation(
            description="Quickstart configs for Nvim LSP",
            homepage="https://github.com/neovim/nvim-lspconfig",
            license="Apache-2.0",
        ),
        fetched_repo=utils.replace(EXAMPLE_REPO, has_submodules=True),
        prefetched=EXAMPLE_PREFETCH,
    )

    _ = fetch_auto.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=expected_token
    )

    _ = prefetch_github.assert_awaited_once_with(
        "neovim",
        "nvim-lspconfig",
        reference=COMMIT_SHA,
        fetch_submodules=True,
        github_token=expected_token,
    )
