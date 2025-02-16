import json
from datetime import datetime
from pathlib import Path

import aiohttp
import attrs
import pytest
from aioresponses import aioresponses
from pytest_mock import MockerFixture

from nupd.exc import HTTPError
from nupd.fetchers import github
from nupd.fetchers.github import (
    Commit,
    GitHubRelease,
    GitHubTag,
    _fetch_latest_release,  # pyright: ignore[reportPrivateUsage]
    _fetch_tags,  # pyright: ignore[reportPrivateUsage]
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
        latest_version=None,
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


async def test_github_prefetch_latest_version_release(
    example_obj: github.GHRepository,
    mocker: MockerFixture,
) -> None:
    release_mock = mocker.patch("nupd.fetchers.github.fetch_latest_release")
    tag_mock = mocker.patch("nupd.fetchers.github.fetch_tags")

    assert (
        await example_obj.prefetch_latest_version(github_token=None)
    ) == attrs.evolve(
        example_obj, latest_version=release_mock.return_value.tag_name
    )

    _ = release_mock.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=None
    )
    _ = tag_mock.assert_not_called()


async def test_github_prefetch_latest_version_tag(
    example_obj: github.GHRepository,
    mocker: MockerFixture,
) -> None:
    release_mock = mocker.patch(
        "nupd.fetchers.github.fetch_latest_release", return_value=None
    )
    tag_mock = mocker.patch(
        "nupd.fetchers.github.fetch_tags",
        return_value=[
            GitHubTag(
                name="v1.6.0",
                commit_sha="bf81bef7d75a0f4a0cf61462b318ea00b3c97cc8",
            )
        ],
    )

    assert (
        await example_obj.prefetch_latest_version(github_token=None)
    ) == attrs.evolve(example_obj, latest_version="v1.6.0")

    _ = release_mock.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=None
    )
    _ = tag_mock.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=None
    )


async def test_github_prefetch_latest_version_nothing(
    example_obj: github.GHRepository,
    mocker: MockerFixture,
) -> None:
    release_mock = mocker.patch(
        "nupd.fetchers.github.fetch_latest_release", return_value=None
    )
    tag_mock = mocker.patch("nupd.fetchers.github.fetch_tags", return_value=[])

    assert (
        await example_obj.prefetch_latest_version(github_token=None)
    ) == example_obj

    _ = release_mock.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=None
    )
    _ = tag_mock.assert_awaited_once_with(
        "neovim", "nvim-lspconfig", github_token=None
    )


async def test_github_prefetch_latest_version_already_fetched(
    example_obj: github.GHRepository,
) -> None:
    o = attrs.evolve(example_obj, latest_version=object())
    assert await o.prefetch_latest_version(github_token=None) is o


async def test_github_fetch_latest_release_success(
    mock_aiohttp: aioresponses,
) -> None:
    with Path("tests/fetchers/github/responses/latest_release.json").open(
        "r"
    ) as f:
        payload = json.load(f)
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/releases/latest",
        payload=payload,
        status=200,
    )

    assert (
        await _fetch_latest_release(
            "neovim", "nvim-lspconfig", github_token=None
        )
    ) == GitHubRelease(
        name="v1.6.0",
        tag_name="v1.6.0",
        created_at=datetime.fromisoformat("2025-01-29T16:07:58Z"),
    )


async def test_github_fetch_latest_release_not_found(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/releases/latest",
        payload={},
        status=404,
    )

    assert (
        await _fetch_latest_release(
            "neovim", "nvim-lspconfig", github_token=None
        )
    ) is None


async def test_github_fetch_latest_release_error(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/releases/latest",
        payload={},
        status=400,
    )

    with pytest.raises(aiohttp.ClientResponseError):
        assert await _fetch_latest_release(
            "neovim", "nvim-lspconfig", github_token=None
        )


async def test_github_fetch_latest_release_error_in_payload(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/releases/latest",
        payload={
            "errors": [
                {"message": "lorem ipsum"},
            ]
        },
        status=200,
    )

    with pytest.raises(HTTPError):
        assert await _fetch_latest_release(
            "neovim", "nvim-lspconfig", github_token=None
        )


async def test_github_fetch_tags_success(
    mock_aiohttp: aioresponses,
) -> None:
    with Path("tests/fetchers/github/responses/tags.json").open("r") as f:
        payload = json.load(f)
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/tags",
        payload=payload,
        status=200,
    )

    assert list(
        await _fetch_tags("neovim", "nvim-lspconfig", github_token=None)
    ) == [
        GitHubTag(
            name="v1.6.0", commit_sha="bf81bef7d75a0f4a0cf61462b318ea00b3c97cc8"
        ),
        GitHubTag(
            name="v1.5.0", commit_sha="637293ce23c6a965d2f11dfbf92f604bb1978052"
        ),
    ]


async def test_github_fetch_tags_empty(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/tags",
        payload=[],
        status=200,
    )

    assert (
        await _fetch_tags("neovim", "nvim-lspconfig", github_token=None)
    ) == []


async def test_github_fetch_tags_not_found(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/tags",
        payload={},
        status=404,
    )

    assert (
        await _fetch_tags("neovim", "nvim-lspconfig", github_token=None)
    ) == []


async def test_github_fetch_tags_error(
    mock_aiohttp: aioresponses,
) -> None:
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/tags",
        payload={},
        status=400,
    )

    with pytest.raises(aiohttp.ClientResponseError):
        assert await _fetch_tags("neovim", "nvim-lspconfig", github_token=None)
