import asyncio
import typing as t

import pytest
from pytest_mock import MockerFixture

from nupd.executables import Executable
from nupd.fetchers.nix_prefetch_url import (
    URLPrefetchError,
    URLPrefetchResult,
    prefetch_obj,
    prefetch_url,
)

if t.TYPE_CHECKING:
    import unittest.mock


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("name", [None, "test-123"])
async def test_prefetch_url(
    mocker: MockerFixture,
    unpack: bool,  # noqa: FBT001
    name: str | None,
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (
        b"079agjlv0hrv7fxnx9ngipx14gyncbkllxrp9cccnh3a50fxcmy7\n"
        b"/nix/store/19zrmhm3m40xxaw81c8cqm6aljgrnwj2-0.8.tar.gz\n",
        b"",
    )
    mock.return_value.returncode = 0

    assert await prefetch_url.func(
        "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
        unpack=unpack,
        name=name,
    ) == URLPrefetchResult(
        hash="079agjlv0hrv7fxnx9ngipx14gyncbkllxrp9cccnh3a50fxcmy7",
        path="/nix/store/19zrmhm3m40xxaw81c8cqm6aljgrnwj2-0.8.tar.gz",
    )

    args = [
        Executable.NIX_PREFETCH_URL,
        "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
        "--print-path",
    ]
    if unpack:
        args.append("--unpack")
    if name:
        args.append("--name")
        args.append(name)

    mock.assert_called_once_with(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("name", [None, "test-123"])
async def test_prefetch_url_return_code_non_zero(
    mocker: MockerFixture,
    unpack: bool,  # noqa: FBT001
    name: str | None,
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (b"stdout", b"stderr")
    mock.return_value.returncode = 1

    with pytest.raises(
        URLPrefetchError,
        match=(
            r"^nix-prefetch-url returned exit code 1\n"
            r"stdout=b'stdout'\nstderr=b'stderr'$"
        ),
    ):
        _ = await prefetch_url.func(
            "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
            unpack=unpack,
            name=name,
        )

    args = [
        Executable.NIX_PREFETCH_URL,
        "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
        "--print-path",
    ]
    if unpack:
        args.append("--unpack")
    if name:
        args.append("--name")
        args.append(name)

    mock.assert_called_once_with(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("name", [None, "test-123"])
async def test_prefetch_url_return_stderr(
    mocker: MockerFixture,
    unpack: bool,  # noqa: FBT001
    name: str | None,
) -> None:
    mock = mocker.patch(
        "asyncio.create_subprocess_exec",
    )
    mock.return_value.communicate.return_value = (b"stdout", b"stderr")
    mock.return_value.returncode = 0

    with pytest.raises(
        URLPrefetchError,
        match=(
            r"^nix-prefetch-url wrote something to stderr! \(unexpected\)\n"
            "stdout=b'stdout'\nstderr=b'stderr'$"
        ),
    ):
        _ = await prefetch_url.func(
            "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
            unpack=unpack,
            name=name,
        )

    args = [
        Executable.NIX_PREFETCH_URL,
        "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
        "--print-path",
    ]
    if unpack:
        args.append("--unpack")
    if name:
        args.append("--name")
        args.append(name)

    mock.assert_called_once_with(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_prefetch_obj(mocker: MockerFixture) -> None:
    mock: unittest.mock.MagicMock = mocker.MagicMock()  # pyright: ignore[reportUnknownVariableType]
    mock_prefetch = mocker.patch(
        "nupd.fetchers.nix_prefetch_url.prefetch_url", spec=prefetch_url.func
    )
    assert await prefetch_obj(mock) == mock_prefetch.return_value
    mock.get_prefetch_url.assert_called_once_with()
    _ = mock_prefetch.assert_awaited_once_with(
        mock.get_prefetch_url.return_value
    )
