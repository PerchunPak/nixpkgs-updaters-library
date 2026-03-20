import typing as t


@t.final
class Executable:
    # these variables are replaced with /nix/store paths
    # so ruff triggers 'line too long' error only during the build
    NURL = "nurl"
    NIX_PREFETCH_URL = "nix-prefetch-url"  # noqa: E501, RUF100
    NIX_PREFETCH_GIT = "nix-prefetch-git"  # noqa: E501, RUF100
