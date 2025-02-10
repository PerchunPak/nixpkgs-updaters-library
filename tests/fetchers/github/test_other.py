import json
from datetime import datetime
from pathlib import Path

import aiohttp
import attrs
import pytest
from aioresponses import aioresponses
from pytest_mock import MockerFixture

from nupd.fetchers import github
from nupd.fetchers.github import (
    Commit,
    _github_does_have_submodules,  # pyright: ignore[reportPrivateUsage]
    _github_prefetch_commit,  # pyright: ignore[reportPrivateUsage]
)


@pytest.fixture
def example_obj() -> github.GHRepository:
    return github.GHRepository(
        owner="neovim",
        repo="nvim-lspconfig",
        branch="master",
        commit=None,
        has_submodules=None,
        meta=github.MetaInformation(
            description="Quickstart configs for Nvim LSP",
            homepage="",
            license="Apache-2.0",
            stars=10794,
            archived=False,
            archived_at=None,
        ),
    )


async def test_prefetch_commit_on_repo_class(
    mocker: MockerFixture, example_obj: github.GHRepository
) -> None:
    mock = mocker.patch(
        "nupd.fetchers.github.github_prefetch_commit",
        return_value=example_obj.commit,
    )
    mock = mocker.patch(
        "nupd.fetchers.github.github_does_have_submodules",
        return_value=example_obj.has_submodules,
    )
    o = object()

    assert (
        await example_obj.prefetch_commit(github_token=o)  # pyright: ignore[reportArgumentType]
    ).commit == mock.return_value
    _ = mock.assert_awaited_once_with(example_obj, github_token=o)


async def test_github_prefetch_commit(
    example_obj: github.GHRepository, mock_aiohttp: aioresponses
) -> None:
    with Path("tests/fetchers/github/responses/prefetch_commit.json").open(
        "r"
    ) as f:
        response = json.load(f)

    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/commits/master",
        payload=response,
    )

    assert (
        await _github_prefetch_commit(example_obj, github_token=None)
    ) == Commit(
        id="b4d65bce97795438ab6e1974b3672c17a4865e3c",
        date=datetime.fromisoformat("2025-01-23T11:38:51Z"),
    )


async def test_prefetch_commit_already_fetched(
    example_obj: github.GHRepository,
) -> None:
    object.__setattr__(example_obj, "commit", "abc")

    assert (
        await _github_prefetch_commit(example_obj, github_token=None) == "abc"
    )


async def test_prefetch_commit_fail(
    example_obj: github.GHRepository, mock_aiohttp: aioresponses
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/commits/master",
        payload={
            "message": "No commit found for SHA: 404",
            "documentation_url": "https://docs.github.com/rest/commits/commits#get-a-commit",
            "status": "422",
        },
        status=404,
    )

    with pytest.raises(aiohttp.ClientResponseError) as error:
        _ = await _github_prefetch_commit(example_obj, github_token=None)
    assert error.match("^404, message='Not Found'.*")


async def test_get_prefetch_url(example_obj: github.GHRepository) -> None:
    object.__setattr__(example_obj, "commit", "abc")

    assert (
        example_obj.get_prefetch_url()
        == "https://github.com/neovim/nvim-lspconfig/archive/abc.tar.gz"
    )


async def test_get_prefetch_url_no_commit(
    example_obj: github.GHRepository,
) -> None:
    with pytest.raises(
        ValueError,
        match="To get archive URL, you have to prefetch commit first",
    ):
        _ = example_obj.get_prefetch_url()


async def test_github_does_have_submodules(
    example_obj: github.GHRepository, mock_aiohttp: aioresponses
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/contents/.gitmodules?ref=master",
        payload={},
        status=200,
    )

    assert (
        await _github_does_have_submodules(example_obj, github_token=None)
    ) is True


async def test_github_does_have_submodules_not_found(
    example_obj: github.GHRepository, mock_aiohttp: aioresponses
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/contents/.gitmodules?ref=master",
        payload={},
        status=404,
    )

    assert (
        await _github_does_have_submodules(example_obj, github_token=None)
    ) is False


async def test_github_does_have_submodules_already_fetched(
    example_obj: github.GHRepository,
) -> None:
    o = object()
    assert (
        await _github_does_have_submodules(
            attrs.evolve(example_obj, has_submodules=o), github_token=None
        )
    ) is o
