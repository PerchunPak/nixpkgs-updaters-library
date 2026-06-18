import pytest
from pytest_mock import MockerFixture

from nupd.fetchers.github import github_fetch_auto, github_full_fetch_auto


async def test_github_fetch_auto_auto_token(mocker: MockerFixture) -> None:
    mock_environ_get = mocker.patch("os.environ.get")
    mock_fetch_graphql = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_graphql",
        mocker.async_stub(),
    )
    mock_fetch_rest = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_rest",
        mocker.async_stub(),
    )

    assert (
        await github_fetch_auto.func("foo", "bar")
        == mock_fetch_graphql.return_value
    )
    _ = mock_fetch_graphql.assert_awaited_once_with(
        "foo", "bar", github_token=mock_environ_get.return_value
    )
    mock_fetch_rest.assert_not_called()


async def test_github_fetch_auto_with_token(mocker: MockerFixture) -> None:
    mock_fetch_graphql = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_graphql",
        mocker.async_stub(),
    )
    mock_fetch_rest = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_rest",
        mocker.async_stub(),
    )

    assert (
        await github_fetch_auto.func("foo", "bar", github_token="baz")
        == mock_fetch_graphql.return_value
    )
    _ = mock_fetch_graphql.assert_awaited_once_with(
        "foo", "bar", github_token="baz"
    )
    mock_fetch_rest.assert_not_called()


async def test_github_fetch_auto_no_token(mocker: MockerFixture) -> None:
    mock_fetch_graphql = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_graphql",
        mocker.async_stub(),
    )
    mock_fetch_rest = mocker.patch(
        "nupd.fetchers.github._fetchers.github_fetch_rest",
        mocker.async_stub(),
    )

    assert (
        await github_fetch_auto.func("foo", "bar", github_token=None)
        == mock_fetch_rest.return_value
    )
    _ = mock_fetch_rest.assert_awaited_once_with(
        "foo", "bar", github_token=None
    )
    mock_fetch_graphql.assert_not_called()


@pytest.mark.parametrize("attribute_overrides", [None, {"foo": "bar"}])
async def test_github_full_fetch_auto(
    mocker: MockerFixture, attribute_overrides: dict[str, str] | None
) -> None:
    mock_replace = mocker.patch("nupd.utils.replace")
    mock_replace.return_value = mocker.async_stub().return_value
    mock_fetch = mocker.patch(
        "nupd.fetchers.github._auto_fetch.github_fetch_auto",
        mocker.async_stub(),
    )

    mock_base = mock_replace if attribute_overrides else mock_fetch
    prefetch_commit = mock_base.return_value.prefetch_commit
    prefetch_last_version = prefetch_commit.return_value.prefetch_latest_version

    assert (
        await github_full_fetch_auto(
            "foo",
            "bar",
            github_token="123",
            attribute_overrides=attribute_overrides,
        )
        == prefetch_last_version.return_value
    )

    mock_fetch.assert_awaited_once_with("foo", "bar", github_token="123")
    prefetch_commit.assert_awaited_once_with()
    prefetch_last_version.assert_awaited_once_with()
    if attribute_overrides:
        mock_replace.assert_called_once_with(
            mock_fetch.return_value, **attribute_overrides
        )
    else:
        mock_replace.assert_not_called()
