import json
from datetime import datetime

import aiohttp
import pytest
from aioresponses import aioresponses

from nupd.fetchers.github import GHRepository, MetaInformation, github_fetch_graphql

LSPCONFIG_RESPONSE = GHRepository(
    owner="neovim",
    repo="nvim-lspconfig",
    branch="master",
    commit="6a5ed22255bbe10104ff9b72c55ec2e233a8e571",
    meta=MetaInformation(
        description="Quickstart configs for Nvim LSP",
        homepage="",
        license="Apache-2.0",
        stars=10794,
        topics=[
            "language-server",
            "language-server-protocol",
            "lsp",
            "neovim",
            "nvim",
            "plugin",
            "vim",
        ],
        archived=False,
        archived_at=None,
    ),
)


async def test_lspconfig(mock_aiohttp: aioresponses) -> None:
    with open("tests/fetchers/github/responses/graphql_lspconfig.json", "r") as f:
        response = json.load(f)  # pyright: ignore[reportAny]
    mock_aiohttp.post(  # pyright: ignore[reportUnknownMemberType]
        "https://api.github.com/graphql", payload=response
    )

    result = await github_fetch_graphql(
        "neovim", "nvim-lspconfig", github_token="TOKEN"
    )
    assert result == LSPCONFIG_RESPONSE


async def test_archived(mock_aiohttp: aioresponses) -> None:
    with open("tests/fetchers/github/responses/graphql_archived.json", "r") as f:
        response = json.load(f)  # pyright: ignore[reportAny]
    mock_aiohttp.post(  # pyright: ignore[reportUnknownMemberType]
        "https://api.github.com/graphql", payload=response
    )

    result = await github_fetch_graphql("PerchunPak", "mcph", github_token="TOKEN")
    assert result == GHRepository(
        owner="PerchunPak",
        repo="mcph",
        branch="master",
        commit="693eb6aa038f832dc614052e6b98bf107f9fcb26",
        meta=MetaInformation(
            description="Minecraft plugin helper, updates and checks versions of all plugins on a server!",
            homepage=None,
            license="AGPL-3.0",
            stars=1,
            topics=[],
            archived=True,
            archived_at=datetime.fromisoformat("2023-06-01T18:53:47Z"),
        ),
    )


async def test_404(mock_aiohttp: aioresponses) -> None:
    with open("tests/fetchers/github/responses/graphql_404.json", "r") as f:
        response = json.load(f)  # pyright: ignore[reportAny]
    mock_aiohttp.post(  # pyright: ignore[reportUnknownMemberType]
        "https://api.github.com/graphql", payload=response, status=404
    )

    with pytest.raises(aiohttp.ClientResponseError) as error:
        _ = await github_fetch_graphql("aaaa", "bbbb", github_token="TOKEN")

    assert error.match("^404, message='Not Found'.*")
