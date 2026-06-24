import contextlib
import re

from packaging.version import InvalidVersion, Version, parse as parse_version

from nupd.fetchers.github._models import GHRepository
from nupd.models import NupdModel

SHA1_REGEX = re.compile("^[0-9a-f]{5,40}$")


class ResolvedVersion(NupdModel, frozen=True):
    version: str
    """Nix-formatted version, e.g. ``0-unstable-2026-06-18``."""
    reference: str
    """Git reference, e.g. ``v1.6.0`` or ``8f7df72ae``."""

    @property
    def is_commit(self) -> bool:
        """Is ``reference`` a commit."""
        return SHA1_REGEX.fullmatch(self.reference) is not None


async def version_by_commit(repo: GHRepository) -> ResolvedVersion:
    """Resolve version to ``0-unstable-2026-06-18``.

    Automatically calls :meth:`GHRepository.prefetch_commit`.
    """
    repo = await repo.prefetch_commit()
    assert repo.commit is not None

    version = None
    if repo.latest_version:
        with contextlib.suppress(InvalidVersion):
            version = parse_version(repo.latest_version)

    return ResolvedVersion(
        version=f"{version or 0}-unstable-{repo.commit.date.date()}",
        reference=repo.commit.id,
    )


async def version_by_tag(repo: GHRepository) -> ResolvedVersion:
    """Resolve version to ``1.2.3``.

    Automatically calls :meth:`GHRepository.prefetch_latest_version`,
    and falls back to :func:`.version_by_commit` if there is no tag.
    """
    repo = await repo.prefetch_latest_version()
    if not repo.latest_version:
        return await version_by_commit(repo)

    version: Version | None = None
    with contextlib.suppress(InvalidVersion):
        version = parse_version(repo.latest_version)

    return ResolvedVersion(
        version=str(version) if version else repo.latest_version,
        reference=repo.latest_version,
    )
