import pytest
from pytest_mock import MockerFixture

from nupd.fetchers.nix_prefetch import URLPrefetchResult, prefetch_url


@pytest.mark.parametrize("unpack", [True, False])
@pytest.mark.parametrize("name", [None, "test-123"])
async def test_prefetch_url(
    mocker: MockerFixture,
    unpack: bool,  # noqa: FBT001
    name: str | None,
) -> None:
    mock = mocker.patch(
        "subprocess.check_output",
        return_value=(
            "079agjlv0hrv7fxnx9ngipx14gyncbkllxrp9cccnh3a50fxcmy7\n"
            "/nix/store/19zrmhm3m40xxaw81c8cqm6aljgrnwj2-0.8.tar.gz\n"
        ),
    )

    assert await prefetch_url(
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

    # NOTE: if we change `text=True` in the future,
    # change input in tests to bytes!
    mock.assert_called_once_with(args, shell=False, text=True)
