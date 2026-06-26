import asyncio
import collections.abc as c
import contextlib
import re

from joblib import expires_after
from loguru import logger
from packaging.version import InvalidVersion, Version, parse as parse_version

from nupd import exc, utils
from nupd.executables import Executable
from nupd.models import NupdModel

NON_RELEASE_TAG_PREFIXES = ("pre-",)
RELEASE_VERSION_PATTERN = re.compile(r"^[^\d]*(\d[\w.@+-]*)$")


class ListGitTagsError(exc.NetworkError): ...


class GitTag(NupdModel, frozen=True):
    revision: str
    """Commit SHA."""
    reference: str
    """Tag reference, e.g. ``v1.6.0``."""

    @property
    def parsed(self) -> Version | None:
        """SemVer version parsed by `packaging.version <https://packaging.pypa.io/en/stable/version.html>`_."""
        with contextlib.suppress(InvalidVersion):
            return parse_version(self.reference)


@utils.restore_docstring_from_memorized_function
@utils.memory.cache(cache_validation_callback=expires_after(hours=3))
async def list_git_tags(
    url: str, *, additional_arguments: c.Iterable[str] | None = None
) -> list[GitTag]:
    """List Git tags, without cloning the repository.

    Internally uses `git ls-remote <https://git-scm.com/docs/git-ls-remote>`_.

    Parameters:
        url: Repository URL.
        additional_arguments:
            Additional arguments that will be passed to ``git ls-remote``.
    """
    logger.debug(f"Listing tags for {url}")

    if additional_arguments is None:
        additional_arguments = []
    additional_arguments = list(additional_arguments)

    process = await asyncio.create_subprocess_exec(
        Executable.GIT,
        "ls-remote",
        "--tags",
        "--refs",
        url,
        *additional_arguments,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise ListGitTagsError(
            f"git ls-remote returned exit code {process.returncode}"
            + f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        raise ListGitTagsError(
            f"git ls-remote wrote something to stderr:\n{stdout=}\n{stderr=}"
        )

    result: list[GitTag] = []

    for row in stdout.decode().splitlines():
        rev, ref = row.split("\t")
        if ref.startswith("refs/tags/"):
            ref = ref.removeprefix("refs/tags/")
            result.append(GitTag(revision=rev, reference=ref))

    return result


def find_latest_tag(tags: c.Iterable[GitTag]) -> GitTag | None:
    """Find latest SemVer tag."""
    best_version: tuple[GitTag, Version] | None = None

    for tag in tags:
        try:
            version = parse_version(tag.reference)
            if best_version is None or version > best_version[1]:
                best_version = (tag, version)
        except InvalidVersion:
            continue

    if best_version is not None:
        return best_version[0]

    return None
