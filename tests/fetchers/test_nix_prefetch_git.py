import asyncio
import datetime
import json

import pytest
from pytest_mock import MockerFixture

from nupd.executables import Executable
from nupd.fetchers.nix_prefetch_git import (
    GitPrefetchError,
    GitPrefetchResult,
    prefetch_git,
)

EXAMPLE_RESPONSE = json.dumps(
    {
        "url": "https://git.sr.ht/~sircmpwn/hare.vim",
        "rev": "e0d38c0563224aa7b0101f64640788691f6c15b9",
        "date": "2024-05-24T12:54:22-05:00",
        "path": "/nix/store/ck5hljy1f47v09g31gfx63w1kdrampab-hare.vim",
        "sha256": "1csc5923acy7awgix0qfkal39v4shzw5vyvw56vkmazvc8n8rqs6",
        "hash": "sha256-RuOMLGL7qzq3KXz7XfiHmuw0qJoOgx4fV8czNUQqTLM=",
        "fetchLFS": False,
        "fetchSubmodules": False,
        "deepClone": False,
        "leaveDotGit": False,
    }
).encode()

EXAMPLE_RESPONSE_OBJ = GitPrefetchResult(
    url="https://git.sr.ht/~sircmpwn/hare.vim",
    rev="e0d38c0563224aa7b0101f64640788691f6c15b9",
    date=datetime.datetime(
        2024,
        5,
        24,
        12,
        54,
        22,
        tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=68400)),
    ),
    path="/nix/store/ck5hljy1f47v09g31gfx63w1kdrampab-hare.vim",
    hash="sha256-RuOMLGL7qzq3KXz7XfiHmuw0qJoOgx4fV8czNUQqTLM=",
    fetch_lfs=False,
    fetch_submodules=False,
    deep_clone=False,
    leave_dot_git=False,
)


@pytest.mark.parametrize(
    "rev", ["e0d38c0563224aa7b0101f64640788691f6c15b9", None]
)
@pytest.mark.parametrize("additional_args", [[], ["a", "b", "c"]])
async def test_prefetch_git(
    mocker: MockerFixture, rev: str, additional_args: list[str]
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (
        EXAMPLE_RESPONSE,
        b"",
    )
    mock.return_value.returncode = 0

    assert (
        await prefetch_git.func(
            "https://git.sr.ht/~sircmpwn/hare.vim",
            revision=rev,
            additional_args=additional_args,
        )
        == EXAMPLE_RESPONSE_OBJ
    )

    args = [
        Executable.NIX_PREFETCH_GIT,
        "https://git.sr.ht/~sircmpwn/hare.vim",
    ]
    if rev:
        args.append(rev)
    args.append("--quiet")
    if additional_args:
        args.extend(additional_args)

    mock.assert_called_once_with(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize(
    "rev", ["e0d38c0563224aa7b0101f64640788691f6c15b9", None]
)
@pytest.mark.parametrize("additional_args", [[], ["a", "b", "c"]])
@pytest.mark.parametrize("return_code", [0, 1])
async def test_prefetch_git_error(
    mocker: MockerFixture,
    rev: str,
    additional_args: list[str],
    return_code: int,
) -> None:
    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.communicate.return_value = (b"stdout", b"stderr")
    mock.return_value.returncode = return_code

    error_msg = (
        "^nix-prefetch-git returned exit code 1\n"
        if return_code == 1
        else "^nix-prefetch-git wrote something to stderr!\n"
    ) + "stdout=b'stdout'\nstderr=b'stderr'$"

    with pytest.raises(
        GitPrefetchError,
        match=error_msg,
    ):
        _ = await prefetch_git.func(
            "https://git.sr.ht/~sircmpwn/hare.vim",
            revision=rev,
            additional_args=additional_args,
        )

    args = [
        Executable.NIX_PREFETCH_GIT,
        "https://git.sr.ht/~sircmpwn/hare.vim",
    ]
    if rev:
        args.append(rev)
    args.append("--quiet")
    if additional_args:
        args.extend(additional_args)

    mock.assert_called_once_with(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
