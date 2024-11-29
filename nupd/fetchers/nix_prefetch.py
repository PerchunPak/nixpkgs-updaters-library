import subprocess

from attrs import define

from nupd.utils import sync_to_async


@define(frozen=True)
class URLPrefetchResult:
    hash: str
    path: str


@sync_to_async
def prefetch_url(
    url: str,
    *,
    unpack: bool = True,
    name: str | None = None,
) -> URLPrefetchResult:
    result = subprocess.check_output(  # noqa: S603
        [
            "nix-prefetch-url",
            url,
            "--print-path",
            *(("--unpack",) if unpack else ()),
            *(("--name", name) if name is not None else ()),
        ],
        shell=False,
        text=True,
    )

    hash, path = result.strip().split("\n")  # noqa: A001
    return URLPrefetchResult(hash=hash, path=path)
