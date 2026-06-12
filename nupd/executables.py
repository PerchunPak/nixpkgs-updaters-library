import typing as t


@t.final
class Executable:
    # these variables are replaced with /nix/store paths
    # so ruff triggers 'line too long' error only during the build
    NURL = "nurl"
    NIX_PREFETCH_URL = "nix-prefetch-url"  # noqa: E501, RUF100
    NIX_PREFETCH_GIT = "nix-prefetch-git"  # noqa: E501, RUF100
    NIX_PREFETCH_GITHUB = "nix-prefetch-github"  # noqa: E501, RUF100
    NIX_PREFETCH_GITHUB_LATEST_RELEASE = "nix-prefetch-github-latest-release"  # noqa: E501, RUF100
    GIT = "git"  # noqa: E501, RUF100
