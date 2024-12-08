import asyncio

import pytest
from pytest_mock import MockerFixture

from nupd.fetchers.nix_prefetch import (
    URLPrefetchError,
    URLPrefetchResult,
    _prefetch_url,  # pyright: ignore[reportPrivateUsage]
)


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

    assert await _prefetch_url(
        "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
        unpack=unpack,
        name=name,
    ) == URLPrefetchResult(
        hash="079agjlv0hrv7fxnx9ngipx14gyncbkllxrp9cccnh3a50fxcmy7",
        path="/nix/store/19zrmhm3m40xxaw81c8cqm6aljgrnwj2-0.8.tar.gz",
    )

    args = [
        "nix-prefetch-url",
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
            "^nix-prefetch-url returned exit code 1\n"
            "stdout=b'stdout'\nstderr=b'stderr'$"
        ),
    ):
        _ = await _prefetch_url(
            "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
            unpack=unpack,
            name=name,
        )

    args = [
        "nix-prefetch-url",
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
        _ = await _prefetch_url(
            "https://github.com/NixOS/patchelf/archive/0.8.tar.gz",
            unpack=unpack,
            name=name,
        )

    args = [
        "nix-prefetch-url",
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
