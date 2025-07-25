import collections.abc as c
import typing as t
from datetime import datetime

import aiohttp
import inject
from loguru import logger
from pydantic import BeforeValidator

from nupd import utils
from nupd.exc import HTTPError
from nupd.models import NupdModel

type OptionalCleanedUpString = t.Annotated[
    str | None,
    BeforeValidator(lambda x: utils.nullify(utils.cleanup_raw_string(x))),
]


class GitHubRelease(NupdModel, frozen=True):
    name: OptionalCleanedUpString
    tag_name: str
    created_at: datetime


class GitHubTag(NupdModel, frozen=True):
    name: str
    commit_sha: str


class MetaInformation(NupdModel, frozen=True):
    description: OptionalCleanedUpString
    homepage: t.Annotated[str | None, BeforeValidator(utils.nullify)]
    license: OptionalCleanedUpString
    stars: int
    archived: bool
    archived_at: datetime | None


class Commit(NupdModel, frozen=True):
    id: str
    date: datetime


class GHRepository(NupdModel, frozen=True):
    owner: str
    repo: str
    branch: str
    meta: MetaInformation
    has_submodules: bool | None
    commit: Commit | None
    latest_version: str | None

    async def prefetch_commit(
        self, *, github_token: str | None = None
    ) -> t.Self:
        commit = await github_prefetch_commit(self, github_token=github_token)
        has_submodules = await github_does_have_submodules(
            self, github_token=github_token
        )
        return utils.replace(self, commit=commit, has_submodules=has_submodules)

    async def prefetch_latest_version(
        self, github_token: str | None = None
    ) -> t.Self:
        """Get the latest version from either releases or tags."""
        if self.latest_version:
            return self

        # First try to get the latest release
        latest_release = await fetch_latest_release(
            self.owner, self.repo, github_token=github_token
        )
        if latest_release is not None:
            return utils.replace(self, latest_version=latest_release.tag_name)

        # If no releases, try to get the latest tag
        tags = await fetch_tags(
            self.owner, self.repo, github_token=github_token
        )
        try:
            # GitHub returns tags in descending order
            latest_tag = next(iter(tags))
            return utils.replace(self, latest_version=latest_tag.name)
        except StopIteration:
            pass
        return self

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"

    def get_prefetch_url(self) -> str:
        if self.commit is None:
            raise ValueError(
                "To get archive URL, you have to prefetch commit first"
            )
        return f"{self.url}/archive/{self.commit}.tar.gz"


@utils.memory.cache
async def github_fetch_graphql(
    owner: str, repo: str, github_token: str
) -> GHRepository:
    session = inject.instance(aiohttp.ClientSession)
    async with session.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {github_token}"},
        json={
            "query": (
                "query {"
                f'  repository(owner: "{owner}", name: "{repo}") {{'
                "    name"
                "    isArchived"
                "    archivedAt"
                "    homepageUrl"
                "    stargazerCount"
                "    description"
                ""
                "    owner {"
                "      login"
                "    }"
                "    licenseInfo {"
                "      spdxId"
                "    }"
                "    latestRelease {"
                "      tagName"
                "    }"
                "    defaultBranchRef {"
                "      name"
                "      target {"
                "        oid"
                "        ... on Commit {"
                "          committedDate"
                "        }"
                "      }"
                "    }"
                "    submodules(first: 1) {"
                "      nodes {"
                "        name"
                "      }"
                "    }"
                "  }"
                "  rateLimit {"
                "    cost"
                "  }"
                "}"
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
        f"Fetching GH:{owner}/{repo} took {data['data']['rateLimit']['cost']} point(s)"
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


@utils.memory.cache
async def github_fetch_rest(
    owner: str, repo: str, *, github_token: str | None
) -> GHRepository:
    """Fetch a GitHub repository using REST API.

    REST API makes GitHub token optional, but it is a lot easier to get rate
    limited. If GitHub token is provided, use GraphQL API instead.

    Do not forget to handle redirects (see `example/simple` directory)!
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
            f"GH repository's ({owner}/{repo}) owner has changed to {new_owner}!"
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


@utils.memory.cache
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


@utils.memory.cache
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


@utils.memory.cache
async def fetch_latest_release(
    owner: str, repo: str, github_token: str | None = None
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


@utils.memory.cache
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
