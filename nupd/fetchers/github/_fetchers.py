import collections.abc as c
from datetime import datetime

import aiohttp
import inject
from joblib import expires_after
from loguru import logger

from nupd import utils
from nupd.exc import HTTPError

from ._models import (
    Commit,
    GHRepository,
    GitHubRelease,
    GitHubTag,
    MetaInformation,
)


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(days=3),
)
async def github_fetch_graphql(
    owner: str, repo: str, *, github_token: str
) -> GHRepository:
    """Fetch a GitHub repository using GraphQL API.

    GraphQL API allows us to include multiple different requests in one,
    which makes it superior for ratelimit-sensitive operations, but it
    requires a token.
    """
    session = inject.instance(aiohttp.ClientSession)
    async with session.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {github_token}"},
        json={
            "query": (
                "query {"
                + f'  repository(owner: "{owner}", name: "{repo}") {{'
                + "    name"
                + "    isArchived"
                + "    archivedAt"
                + "    homepageUrl"
                + "    stargazerCount"
                + "    description"
                + ""
                + "    owner {"
                + "      login"
                + "    }"
                + "    licenseInfo {"
                + "      spdxId"
                + "    }"
                + "    latestRelease {"
                + "      tagName"
                + "    }"
                + "    defaultBranchRef {"
                + "      name"
                + "      target {"
                + "        oid"
                + "        ... on Commit {"
                + "          committedDate"
                + "        }"
                + "      }"
                + "    }"
                + "    submodules(first: 1) {"
                + "      nodes {"
                + "        name"
                + "      }"
                + "    }"
                + "  }"
                + "  rateLimit {"
                + "    cost"
                + "  }"
                + "}"
            )
        },
    ) as response:
        data = await response.json()

        if not response.ok:
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover
        if data.get("errors"):
            logger.error(data)
            raise HTTPError(
                "\n".join(error["message"] for error in data["errors"])
            )

    logger.debug(
        f"Fetching GH:{owner}/{repo} took {data['data']['rateLimit']['cost']} "
        + "point(s)"
    )
    data = data["data"]["repository"]

    if not (
        commit_date := data["defaultBranchRef"]["target"].get("committedDate")
    ):
        raise RuntimeError(
            "You've encountered a weird edge-case. Please open a bug report"
        )
    latest_release = data["latestRelease"]

    return GHRepository(
        owner=data["owner"]["login"],
        repo=data["name"],
        branch=data["defaultBranchRef"]["name"],
        commit=Commit(
            id=data["defaultBranchRef"]["target"]["oid"],
            date=commit_date,
        ),
        latest_version=None
        if not latest_release
        else latest_release["tagName"],
        has_submodules=bool(len(data["submodules"]["nodes"])),
        meta=MetaInformation(
            description=data["description"],
            homepage=data["homepageUrl"],
            license=(data["licenseInfo"] or {}).get("spdxId"),
            stars=data["stargazerCount"],
            archived=data["isArchived"],
            archived_at=datetime.fromisoformat(data["archivedAt"])
            if data["archivedAt"] is not None
            else None,
        ),
    )


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(days=3),
)
async def github_fetch_rest(
    owner: str, repo: str, *, github_token: str | None
) -> GHRepository:
    """Fetch a GitHub repository using REST API.

    REST API makes GitHub token optional, but it is a lot easier to get rate
    limited. If GitHub token is provided, use GraphQL API instead.

    Do not forget to handle redirects!
    """
    session = inject.instance(aiohttp.ClientSession)
    async with session.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}" if github_token else "",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    ) as response:
        data = await response.json()

        if not response.ok:
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover

    new_owner, new_repo = data["owner"]["login"], data["name"]
    if new_owner != owner:
        logger.warning(
            f"GH repository's ({owner}/{repo}) owner has changed to "
            + f"{new_owner}!"
        )
    if new_repo != repo:
        logger.warning(
            f"GH repository's ({owner}/{repo}) name has changed to {new_owner}!"
        )

    return GHRepository(
        owner=new_owner,
        repo=new_repo,
        branch=data["default_branch"],
        commit=None,
        has_submodules=None,
        latest_version=None,
        meta=MetaInformation(
            description=data["description"],
            homepage=data["homepage"],
            license=(data["license"] or {}).get("spdx_id"),
            stars=data["stargazers_count"],
            archived=data["archived"],
            # this may not be always accurate, but it is the closest
            # we can get using REST API. Next time someone will use
            # GraphQL on this repo, it will pick the correct date
            archived_at=datetime.fromisoformat(data["updated_at"])
            if data["archived"]
            else None,
        ),
    )


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(hours=1),
)
async def github_prefetch_commit(
    repo: GHRepository, *, github_token: str | None = None
) -> Commit:
    if repo.commit is not None:
        return repo.commit

    session = inject.instance(aiohttp.ClientSession)
    async with session.get(
        f"https://api.github.com/repos/{repo.owner}/{repo.repo}/commits/{repo.branch}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}" if github_token else "",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    ) as response:
        data = await response.json()

        if not response.ok:
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover

    return Commit(
        id=data["sha"],
        date=datetime.fromisoformat(data["commit"]["author"]["date"]),
    )


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(days=3),
)
async def github_does_have_submodules(
    repo: GHRepository, *, github_token: str | None = None
) -> bool:
    if repo.has_submodules is not None:
        return repo.has_submodules

    session = inject.instance(aiohttp.ClientSession)
    async with session.get(
        f"https://api.github.com/repos/{repo.owner}/{repo.repo}/contents/.gitmodules?ref={repo.branch}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}" if github_token else "",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    ) as response:
        if not response.ok and response.status != 404:
            data = await response.json()
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover

    return response.status != 404


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(hours=1),
)
async def fetch_latest_release(
    owner: str, repo: str, *, github_token: str | None = None
) -> GitHubRelease | None:
    """Fetch the latest release information for this repository."""
    session = inject.instance(aiohttp.ClientSession)

    async with session.get(
        f"https://api.github.com/repos/{owner}/{repo}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {github_token}" if github_token else "",
        },
    ) as response:
        if response.status == 404:
            return None
        data = await response.json()

        if not response.ok:
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover
        if data.get("errors"):
            logger.error(data)
            raise HTTPError(
                "\n".join(error["message"] for error in data["errors"])
            )

    return GitHubRelease(
        name=data.get("name"),
        tag_name=data["tag_name"],
        created_at=datetime.fromisoformat(data["created_at"]),
    )


@utils.restore_docstring_from_memoized_function
@utils.memory.cache(
    ignore=["github_token"],
    cache_validation_callback=expires_after(hours=1),
)
async def fetch_tags(
    owner: str, repo: str, github_token: str | None = None
) -> c.Iterable[GitHubTag]:
    """Get information about a specific release by tag."""
    session = inject.instance(aiohttp.ClientSession)

    async with session.get(
        f"https://api.github.com/repos/{owner}/{repo}/tags",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {github_token}" if github_token else "",
        },
    ) as response:
        if response.status == 404:
            return []
        data = await response.json()

        if not response.ok:
            logger.error(data)
            response.raise_for_status()
            raise RuntimeError("dead code")  # pragma: no cover

    return [
        GitHubTag(name=tag_data["name"], commit_sha=tag_data["commit"]["sha"])
        for tag_data in data
    ]
