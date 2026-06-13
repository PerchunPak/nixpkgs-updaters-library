import asyncio
import datetime as dt
import json
import typing as t
from copy import deepcopy

import pytest
from pytest_mock import MockerFixture

from nupd import utils
from nupd.executables import Executable
from nupd.fetchers.nix_prefetch_github import (
    GithubPrefetchError,
    GithubPrefetchResult,
    prefetch_github,
)

EXAMPLE_RESPONSE = {
    "src": {
        "owner": "SnapXL",
        "repo": "SnapX",
        "rev": "767e54d5e70518f186cbbe51e7b6933bddbb55bd",
        "hash": "sha256-Vy9TUsMCgx0kh8ftz3fwylOjg/DQc/53TPeivkeUuGw=",
    },
    "meta": {
        "commitDate": "2026-06-08",
        "commitTimeOfDay": "21:45:51",
    },
}

EXAMPLE_RESPONSE_OBJ = GithubPrefetchResult(
    owner="SnapXL",
    repo="SnapX",
    rev="767e54d5e70518f186cbbe51e7b6933bddbb55bd",
    hash="sha256-Vy9TUsMCgx0kh8ftz3fwylOjg/DQc/53TPeivkeUuGw=",
    commit_date=dt.datetime(2026, 6, 8, 21, 45, 51),  # noqa: DTZ001 # test fails if timezone here is specified
)


@pytest.mark.parametrize(
    "rev", ["767e54d5e70518f186cbbe51e7b6933bddbb55bd", None]
)
@pytest.mark.parametrize("with_meta", [False, True])
@pytest.mark.parametrize("additional_arguments", [[], ["a", "b", "c"]])
async def test_prefetch_github(
    mocker: MockerFixture,
    rev: str,
    with_meta: bool,
    additional_arguments: list[str],
) -> None:
    if with_meta:
        response, response_obj = EXAMPLE_RESPONSE, EXAMPLE_RESPONSE_OBJ
    else:
        response = EXAMPLE_RESPONSE["src"]
        response_obj = utils.replace(EXAMPLE_RESPONSE_OBJ, commit_date=None)

    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.communicate.return_value = (
        json.dumps(response).encode(),
        b"",
    )
    mock.return_value.returncode = 0

    assert (
        await prefetch_github.func(
            "SnapXL",
            "SnapX",
            revision=rev,
            with_meta=with_meta,
            additional_arguments=additional_arguments,
        )
        == response_obj
    )

    args = [
        Executable.NIX_PREFETCH_GITHUB,
        "SnapXL",
        "SnapX",
    ]
    if with_meta:
        args.append("--meta")
    if rev:
        args.append("--rev")
        args.append(rev)
    if additional_arguments:
        args.extend(additional_arguments)

    mock.assert_called_once_with(
        *args,
        env=None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_prefetch_github_latest_release(mocker: MockerFixture) -> None:
    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.communicate.return_value = (
        json.dumps(EXAMPLE_RESPONSE["src"]).encode(),
        b"",
    )
    mock.return_value.returncode = 0

    assert await prefetch_github.func(
        "SnapXL",
        "SnapX",
        latest_release=True,
    ) == utils.replace(EXAMPLE_RESPONSE_OBJ, commit_date=None)

    args = [
        Executable.NIX_PREFETCH_GITHUB_LATEST_RELEASE,
        "SnapXL",
        "SnapX",
    ]

    mock.assert_called_once_with(
        *args,
        env=None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("with_meta", [False, True])
@pytest.mark.parametrize(
    "attribute", ["fetch_submodules", "leave_dot_git", "deep_clone"]
)
async def test_prefetch_github_extra_attributes(
    mocker: MockerFixture, with_meta: bool, attribute: str
) -> None:
    response: dict[str, t.Any] = deepcopy(EXAMPLE_RESPONSE)
    response["src"][attribute] = True
    response_obj = utils.replace(
        EXAMPLE_RESPONSE_OBJ,
        **({"commit_date": None} if not with_meta else {}),
        fetch_submodules=attribute == "fetch_submodules",
        leave_dot_git=attribute == "leave_dot_git",
        deep_clone=attribute == "deep_clone",
    )

    if not with_meta:
        response = response["src"]

    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.communicate.return_value = (
        json.dumps(response).encode(),
        b"",
    )
    mock.return_value.returncode = 0

    assert (
        await prefetch_github.func(
            "SnapXL",
            "SnapX",
            with_meta=with_meta,
            fetch_submodules=attribute == "fetch_submodules",
            leave_dot_git=attribute == "leave_dot_git",
            deep_clone=attribute == "deep_clone",
        )
        == response_obj
    )

    args = [
        Executable.NIX_PREFETCH_GITHUB,
        "SnapXL",
        "SnapX",
    ]
    if with_meta:
        args.append("--meta")

    match attribute:
        case "fetch_submodules":
            args.append("--fetch-submodules")
        case "leave_dot_git":
            args.append("--leave-dot-git")
        case "deep_clone":
            args.append("--deep-clone")
        case _:
            raise NotImplementedError

    mock.assert_called_once_with(
        *args,
        env=None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize(
    "rev", ["767e54d5e70518f186cbbe51e7b6933bddbb55bd", None]
)
@pytest.mark.parametrize("additional_arguments", [None, ["a", "b", "c"]])
@pytest.mark.parametrize("return_code", [0, 1])
async def test_prefetch_github_error(
    mocker: MockerFixture,
    rev: str,
    additional_arguments: list[str] | None,
    return_code: int,
) -> None:
    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.communicate.return_value = (b"stdout", b"stderr")
    mock.return_value.returncode = return_code

    error_msg = (
        "^nix-prefetch-github returned exit code 1"
        if return_code == 1
        else "^nix-prefetch-github wrote something to stderr! \\(unexpected\\)"
    ) + "\nstdout=b'stdout'\nstderr=b'stderr'$"

    with pytest.raises(
        GithubPrefetchError,
        match=error_msg,
    ):
        _ = await prefetch_github.func(
            "SnapXL",
            "SnapX",
            revision=rev,
            additional_arguments=additional_arguments,
        )

    args = [
        Executable.NIX_PREFETCH_GITHUB,
        "SnapXL",
        "SnapX",
    ]
    if rev:
        args.append("--rev")
        args.append(rev)
    if additional_arguments:
        args.extend(additional_arguments)

    mock.assert_called_once_with(
        *args,
        env=None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
