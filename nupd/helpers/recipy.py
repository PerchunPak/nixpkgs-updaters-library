import abc
import typing as t

from pydantic import ConfigDict, alias_generators

from nupd.models import NupdModel
from nupd.utils import FrozenDict


class NixMetaInformation(NupdModel, frozen=True):
    """Class, representing Nix's ``meta`` attribute set.

    .. seealso:: https://nixos.org/manual/nixpkgs/unstable/#chap-meta
    """

    model_config: ConfigDict = ConfigDict(  # pyright: ignore[reportIncompatibleVariableOverride]
        alias_generator=alias_generators.to_camel,
        validate_by_name=True,
    )

    # https://nixos.org/manual/nixpkgs/unstable/#sec-standard-meta-attributes
    description: str | None = None
    long_description: str | None = None
    branch: str | None = None
    homepage: str | None = None
    download_page: str | None = None
    changelog: str | None = None
    license: str | None = None
    source_provenance: list[str] | None = None
    maintainers: list[str] | None = None
    teams: list[str] | None = None
    main_program: str | None = None
    priority: int | None = None
    platforms: list[str] | None = None
    bad_platforms: list[str] | None = None
    timeout: int | None = None
    hydra_platforms: list[str] | None = None
    broken: bool | None = None


class ABCRecipy(NupdModel, abc.ABC, frozen=True):
    """Base class for all recipes."""

    version: str
    fetcher: str
    fetcher_args: FrozenDict[str, t.Any]
    meta: NixMetaInformation
