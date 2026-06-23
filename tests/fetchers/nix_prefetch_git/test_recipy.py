import datetime as dt

import pytest
from frozendict import frozendict
from pytest_mock import MockerFixture

from nupd.fetchers.nix_prefetch_git import (
    GitPrefetchResult,
    GitPrefetchVersioning,
    GitRecipy,
)
from nupd.helpers.git import GitTag
from nupd.helpers.recipy import NixMetaInformation

EXAMPLE_PREFETCH = GitPrefetchResult(
    url="https://git.sr.ht/~sircmpwn/hare.vim",
    rev="e0d38c0563224aa7b0101f64640788691f6c15b9",
    date=dt.datetime.fromisoformat("2024-05-24T12:54:22-05:00"),
    path="/nix/store/ck5hljy1f47v09g31gfx63w1kdrampab-hare.vim",
    hash="sha256-RuOMLGL7qzq3KXz7XfiHmuw0qJoOgx4fV8czNUQqTLM=",
    fetch_lfs=False,
    fetch_submodules=False,
    deep_clone=False,
    leave_dot_git=False,
)


@pytest.mark.parametrize(
    ("strategy", "version"),
    [
        (GitPrefetchVersioning.LATEST_TAG, "1.6.0"),
        (GitPrefetchVersioning.BY_COMMIT, "1.6.0-unstable-2024-05-24"),
    ],
)
async def test_git_recipy_fetch(
    mocker: MockerFixture,
    strategy: GitPrefetchVersioning,
    version: str,
) -> None:
    list_git_tags = mocker.patch(
        "nupd.helpers.git.list_git_tags", mocker.async_stub()
    )
    list_git_tags.return_value = [
        GitTag(
            revision="e0d38c0563224aa7b0101f64640788691f6c15b9",
            reference="v1.6.0",
        ),
    ]
    nix_prefetch_git = mocker.patch(
        "nupd.fetchers.nix_prefetch_git.prefetch_git",
        mocker.async_stub(),
    )
    nix_prefetch_git.return_value = EXAMPLE_PREFETCH

    fetcher_args = EXAMPLE_PREFETCH.to_fetcher_args()
    if strategy == GitPrefetchVersioning.LATEST_TAG:
        fetcher_args.pop("rev")
        fetcher_args["tag"] = "v1.6.0"

    # assertions
    assert await GitRecipy.fetch(
        "https://git.sr.ht/~sircmpwn/hare.vim",
        versioning_strategy=strategy,
        additional_args={"foo": "bar"},
    ) == GitRecipy(
        version=version,
        fetcher="fetchgit",
        fetcher_args=frozendict(fetcher_args),
        meta=NixMetaInformation(),
        prefetched=EXAMPLE_PREFETCH,
    )

    list_git_tags.assert_awaited_once_with(
        "https://git.sr.ht/~sircmpwn/hare.vim"
    )
    nix_prefetch_git.assert_awaited_once_with(
        "https://git.sr.ht/~sircmpwn/hare.vim",
        revision=None
        if strategy == GitPrefetchVersioning.BY_COMMIT
        else "v1.6.0",
        additional_args={"foo": "bar"},
    )
