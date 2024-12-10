import pytest
from pytest_mock import MockerFixture

from nupd.fetchers import github


@pytest.fixture
def example_obj() -> github.GHRepository:
    return github.GHRepository(
        owner="neovim",
        repo="nvim-lspconfig",
        branch="master",
        commit=None,
        meta=github.MetaInformation(
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


async def test_prefetch_commit(
    mocker: MockerFixture, example_obj: github.GHRepository
) -> None:
    mock = mocker.patch("nupd.fetchers.nix_prefetch.prefetch_url")

    assert await example_obj.prefetch_commit() == mock.return_value.hash
    _ = mock.assert_awaited_once_with(
        "https://github.com/neovim/nvim-lspconfig/archive/master.tar.gz"
    )


async def test_prefetch_commit_already_fetched(
    mocker: MockerFixture, example_obj: github.GHRepository
) -> None:
    mock = mocker.patch("nupd.fetchers.nix_prefetch.prefetch_url")
    example_obj.commit = "abc"

    assert await example_obj.prefetch_commit() == "abc"
    _ = mock.assert_not_called()


async def test_get_prefetch_url(example_obj: github.GHRepository) -> None:
    example_obj.commit = "abc"

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
