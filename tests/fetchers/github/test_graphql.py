import copy
import json
from datetime import datetime
from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from nupd.fetchers.github import (
    Commit,
    GHRepository,
    MetaInformation,
    _github_fetch_graphql,  # pyright: ignore[reportPrivateUsage]
)

LSPCONFIG_RESPONSE = GHRepository(
    owner="neovim",
    repo="nvim-lspconfig",
    branch="master",
    commit=Commit(
        id="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
        date=datetime.fromisoformat("2023-06-01T18:52:58Z"),
    ),
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


async def test_lspconfig(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/graphql_lspconfig.json").open(
        "r"
    ) as f:
        response = json.load(f)
    mock_aiohttp.post("https://api.github.com/graphql", payload=response)

    result = await _github_fetch_graphql(
        "neovim", "nvim-lspconfig", github_token="TOKEN"
    )
    assert result == LSPCONFIG_RESPONSE


async def test_archived(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/graphql_archived.json").open(
        "r"
    ) as f:
        response = json.load(f)
    mock_aiohttp.post("https://api.github.com/graphql", payload=response)

    result = await _github_fetch_graphql(
        "PerchunPak", "mcph", github_token="TOKEN"
    )
    assert result == GHRepository(
        owner="PerchunPak",
        repo="mcph",
        branch="master",
        commit=Commit(
            id="693eb6aa038f832dc614052e6b98bf107f9fcb26",
            date=datetime.fromisoformat("2023-06-01T18:52:58Z"),
        ),
        has_submodules=False,
        meta=MetaInformation(
            description="Minecraft plugin helper, updates and checks versions of all plugins on a server!",
            homepage=None,
            license="AGPL-3.0",
            stars=1,
            archived=True,
            archived_at=datetime.fromisoformat("2023-06-01T18:53:47Z"),
        ),
    )


async def test_404(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/graphql_404.json").open(
        "r"
    ) as f:
        response = json.load(f)
    mock_aiohttp.post(
        "https://api.github.com/graphql", payload=response, status=404
    )

    with pytest.raises(aiohttp.ClientResponseError) as error:
        _ = await _github_fetch_graphql("aaaa", "bbbb", github_token="TOKEN")

    assert error.match("^404, message='Not Found'.*")


async def test_no_license(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/graphql_lspconfig.json").open(
        "r"
    ) as f:
        response = json.load(f)
        response["data"]["repository"]["licenseInfo"] = None
    mock_aiohttp.post("https://api.github.com/graphql", payload=response)

    result = await _github_fetch_graphql(
        "neovim", "nvim-lspconfig", github_token="TOKEN"
    )
    expected_response = copy.deepcopy(LSPCONFIG_RESPONSE)
    object.__setattr__(expected_response.meta, "license", None)
    assert result == expected_response
