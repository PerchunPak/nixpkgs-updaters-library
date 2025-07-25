import asyncio
import json
import typing as t

import pytest
from frozendict import frozendict
from pytest_mock import MockerFixture

from nupd.executables import Executable
from nupd.fetchers.nurl import FETCHERS, NurlError, NurlResult, nurl, nurl_parse

EXAMPLE_RESPONSE: dict[str, t.Any] = {
    "args": {
        "hash": "sha256-oKOqnHaizo209cXHkCbPVFjBjsc9GJ/Og+9rCB8YGfU=",
        "owner": "nix-community",
        "repo": "patsh",
        "rev": "65d3e558a6d2270e42f6b28f03092c11f24cbb20",
    },
    "fetcher": "fetchFromGitHub",
}
EXAMPLE_RESPONSE_OBJ = NurlResult(
    args=frozendict(
        hash="sha256-oKOqnHaizo209cXHkCbPVFjBjsc9GJ/Og+9rCB8YGfU=",
        owner="nix-community",
        repo="patsh",
        rev="65d3e558a6d2270e42f6b28f03092c11f24cbb20",
    ),
    fetcher="fetchFromGitHub",
)


@pytest.mark.parametrize("revision", ["aaaaaa", None])
@pytest.mark.parametrize("additional_arguments", [["--json"], []])
@pytest.mark.parametrize("submodules", [False, True])
@pytest.mark.parametrize("fetcher", ["fetchFromGitLab", None])
@pytest.mark.parametrize("fallback", ["fetchFromGitLab", None])
async def test_nurl_basic(
    mocker: MockerFixture,
    revision: str | None,
    additional_arguments: list[str],
    submodules: bool,  # noqa: FBT001
    fetcher: FETCHERS | None,
    fallback: FETCHERS | None,
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (
        json.dumps(EXAMPLE_RESPONSE).encode(),
        b"stderr",
    )
    mock.return_value.returncode = 0

    assert (
        await nurl.func(
            "https://github.com/nix-community/patsh",
            revision=revision,
            additional_arguments=additional_arguments
            if len(additional_arguments) > 0
            else None,
            submodules=submodules,
            fetcher=fetcher,
            fallback=fallback,
        )
        == EXAMPLE_RESPONSE_OBJ
    )

    args = [
        Executable.NURL,
        "https://github.com/nix-community/patsh",
    ]
    if revision:
        args.append(revision)
    if submodules:
        args.append("--submodules=true")
    if fetcher:
        args.append("--fetcher")
        args.append(fetcher)
    if fallback:
        args.append("--fallback")
        args.append(fallback)
    if len(additional_arguments) > 0:
        args.extend(additional_arguments)

    mock.assert_called_once_with(
        *args,
        "--json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_nurl_return_code_non_zero(
    mocker: MockerFixture,
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (b"stdout", b"stderr")
    mock.return_value.returncode = 1

    with pytest.raises(
        NurlError,
        match=(
            "^nurl returned exit code 1\nstdout=b'stdout'\nstderr=b'stderr'$"
        ),
    ):
        _ = await nurl.func("https://github.com/NixOS/patsh")

    mock.assert_called_once_with(
        Executable.NURL,
        "https://github.com/NixOS/patsh",
        "--json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("additional_args", [["--help"], []])
async def test_nurl_parse(
    mocker: MockerFixture, additional_args: list[str]
) -> None:
    mock = mocker.patch(
        "nupd.fetchers.nurl.nurl",
        spec=nurl.func,
        return_value=EXAMPLE_RESPONSE_OBJ,
    )

    assert (
        await nurl_parse(
            "https://github.com/NixOS/patsh",
            additional_arguments=additional_args if additional_args else None,
            submodules=True,
        )
        is EXAMPLE_RESPONSE_OBJ
    )

    mock.assert_called_once_with(
        url="https://github.com/NixOS/patsh",
        revision=None,
        additional_arguments=["--parse", *additional_args],
        submodules=True,
        fetcher=None,
        fallback=None,
    )
