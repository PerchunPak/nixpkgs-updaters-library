import copy
import json
from datetime import datetime
from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from nupd.fetchers.github import (
    GHRepository,
    MetaInformation,
    github_fetch_rest,
)

LSPCONFIG_RESPONSE = GHRepository(
    owner="neovim",
    repo="nvim-lspconfig",
    branch="master",
    commit=None,
    has_submodules=None,
    latest_version=None,
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
    with Path("tests/fetchers/github/responses/rest_lspconfig.json").open(
        "r"
    ) as f:
        response = json.load(f)
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig", payload=response
    )

    result = await github_fetch_rest.func(
        "neovim", "nvim-lspconfig", github_token=None
    )
    assert result == LSPCONFIG_RESPONSE


async def test_archived(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/rest_archived.json").open(
        "r"
    ) as f:
        response = json.load(f)
    mock_aiohttp.get(
        "https://api.github.com/repos/PerchunPak/mcph", payload=response
    )

    result = await github_fetch_rest.func(
        "PerchunPak", "mcph", github_token=None
    )
    assert result == GHRepository(
        owner="PerchunPak",
        repo="mcph",
        branch="master",
        commit=None,
        has_submodules=None,
        latest_version=None,
        meta=MetaInformation(
            description="Minecraft plugin helper, updates and checks versions of all plugins on a server!",
            homepage=None,
            license="AGPL-3.0",
            stars=1,
            archived=True,
            archived_at=datetime.fromisoformat("2023-09-11T15:35:30Z"),
        ),
    )


async def test_404(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/rest_404.json").open("r") as f:
        response = json.load(f)
    mock_aiohttp.get(
        "https://api.github.com/repos/aaaa/bbbb", payload=response, status=404
    )

    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig/releases/latest",
        status=404,
    )

    with pytest.raises(aiohttp.ClientResponseError) as error:
        _ = await github_fetch_rest.func("aaaa", "bbbb", github_token=None)

    assert error.match("^404, message='Not Found'.*")


async def test_redirect(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/rest_lspconfig.json").open(
        "r"
    ) as f:
        response = json.load(f)

    mock_aiohttp.get(
        "https://api.github.com/repos/nvim/lspconfig",
        headers={"Location": "/repos/neovim/nvim-lspconfig"},
        status=307,
    )
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig", payload=response
    )

    result = await github_fetch_rest.func(
        "nvim", "lspconfig", github_token=None
    )
    assert result == LSPCONFIG_RESPONSE


async def test_no_license(mock_aiohttp: aioresponses) -> None:
    with Path("tests/fetchers/github/responses/rest_lspconfig.json").open(
        "r"
    ) as f:
        response = json.load(f)
        response["license"] = None
    mock_aiohttp.get(
        "https://api.github.com/repos/neovim/nvim-lspconfig", payload=response
    )

    result = await github_fetch_rest.func(
        "neovim", "nvim-lspconfig", github_token=None
    )
    expected_response = copy.deepcopy(LSPCONFIG_RESPONSE)
    object.__setattr__(expected_response.meta, "license", None)
    assert result == expected_response
