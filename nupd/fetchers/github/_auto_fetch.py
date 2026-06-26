import os
import typing as t

from joblib import expires_after

from nupd import utils

from . import _fetchers as fetchers  # pyright: ignore[reportPrivateUsage]
from ._models import GHRepository


@utils.restore_docstring_from_memorized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(days=3),
)
async def github_fetch_auto(
    owner: str,
    repo: str,
    *,
    github_token: str | None = "auto",  # noqa: S107 # possible hardcoded password
) -> GHRepository:
    """Fetch a GitHub repository with automatically resolved API and token.

    If ``github_token`` is ``"auto"``, the function tries to get the token from
    ``os.environ["GITHUB_TOKEN"]``. If ``github_token`` is present, this
    function will call :func:`.github_fetch_graphql`, otherwise it will call
    :func:`github_fetch_rest`.
    """
    if github_token == "auto":  # noqa: S105 # possible hardcoded password
        github_token = os.environ.get("GITHUB_TOKEN")

    if github_token:
        return await fetchers.github_fetch_graphql(
            owner, repo, github_token=github_token
        )
    return await fetchers.github_fetch_rest(owner, repo, github_token=None)


async def github_full_fetch_auto(
    owner: str,
    repo: str,
    *,
    github_token: str | None = "auto",  # noqa: S107 # possible hardcoded password
    attribute_overrides: dict[str, t.Any] | None = None,
) -> GHRepository:
    """The same as :func:`.github_fetch_auto`, but fetches all information.

    Parameters:
        attribute_overrides:
            Calls :func:`utils.replace() <nupd.utils.replace>` right after
            a call to :func:`.github_fetch_auto` and before fetching the rest
            of the arguments.
    """  # noqa: D401 # imperative mood
    result = await github_fetch_auto(owner, repo, github_token=github_token)
    if attribute_overrides:
        result = utils.replace(result, **attribute_overrides)
    result = await result.prefetch_commit()
    result = await result.prefetch_latest_version()
    return result
