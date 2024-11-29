from datetime import datetime

import aiohttp
import inject
from attrs import define
from loguru import logger

from nupd.exc import HTTPError
from nupd.fetchers.nix_prefetch import prefetch_url


@define
class MetaInformation:
    description: str | None
    homepage: str | None
    license: str | None
    stars: int
    topics: list[str]
    archived: bool
    archived_at: datetime | None

    def __attrs_post_init__(self) -> None:
        self.topics = sorted(self.topics)


@define
class GHRepository:
    owner: str
    repo: str
    branch: str
    commit: str | None

    meta: MetaInformation

    async def prefetch_commit(self) -> str:
        if self.commit is not None:
            return self.commit

        self.commit = commit = (
            await prefetch_url(
                f"https://github.com/{self.owner}/{self.repo}/archive/{self.branch}.tar.gz"
            )
        ).hash
        return commit


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
                "    defaultBranchRef {"
                "      name"
                "      target {"
                "        oid"
                "      }"
                "    }"
                "    repositoryTopics(first:100) {"
                "      nodes {"
                "        topic {"
                "          name"
                "        }"
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
            raise Exception  # dead code # noqa: TRY002
        if data.get("errors"):
            logger.error(data)
            raise HTTPError(
                "\n".join(error["message"] for error in data["errors"])
            )

    logger.debug(
        f"Fetching GH:{owner}/{repo} took {data["data"]["rateLimit"]["cost"]} point(s)"
    )
    data = data["data"]["repository"]

    return GHRepository(
        owner=data["owner"]["login"],
        repo=data["name"],
        branch=data["defaultBranchRef"]["name"],
        commit=data["defaultBranchRef"]["target"]["oid"],
        meta=MetaInformation(
            description=data["description"],
            homepage=data["homepageUrl"],
            license=data["licenseInfo"]["spdxId"],
            stars=data["stargazerCount"],
            topics=[
                node["topic"]["name"]
                for node in data["repositoryTopics"]["nodes"]
            ],
            archived=data["isArchived"],
            archived_at=datetime.fromisoformat(data["archivedAt"])
            if data["archivedAt"] is not None
            else None,
        ),
    )


async def github_fetch_rest(
    owner: str, repo: str, *, github_token: str | None
) -> GHRepository:
    """
    Fetch a GitHub repository using REST API.

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
            raise Exception  # dead code # noqa: TRY002

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
        meta=MetaInformation(
            description=data["description"],
            homepage=data["homepage"],
            license=data["license"]["spdx_id"],
            stars=data["stargazers_count"],
            topics=data["topics"],
            archived=data["archived"],
            # this may not be always accurate, but it is the closest
            # we can get using REST API. Next time someone will use
            # GraphQL on this repo, it will pick the correct date
            archived_at=datetime.fromisoformat(data["updated_at"])
            if data["archived"]
            else None,
        ),
    )
