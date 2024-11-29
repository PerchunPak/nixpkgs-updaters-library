from datetime import datetime

import aiohttp
import inject
from attrs import define
from loguru import logger

from nupd.exc import HTTPError


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
        data = await response.json()  # pyright: ignore[reportAny]

        if not response.ok:
            logger.error(data)  # pyright: ignore[reportAny]
            response.raise_for_status()
            raise Exception()  # dead code
        elif data.get("errors"):  # pyright: ignore[reportAny]
            logger.error(data)  # pyright: ignore[reportAny]
            raise HTTPError(
                "\n".join(error["message"] for error in data["errors"])  # pyright: ignore[reportAny]
            )

    logger.debug(
        f"Fetching GH:{owner}/{repo} took {data["data"]["rateLimit"]["cost"]} point(s)"
    )
    data = data["data"]["repository"]  # pyright: ignore[reportAny]

    return GHRepository(
        owner=data["owner"]["login"],  # pyright: ignore[reportAny]
        repo=data["name"],  # pyright: ignore[reportAny]
        branch=data["defaultBranchRef"]["name"],  # pyright: ignore[reportAny]
        commit=data["defaultBranchRef"]["target"]["oid"],  # pyright: ignore[reportAny]
        meta=MetaInformation(
            description=data["description"],  # pyright: ignore[reportAny]
            homepage=data["homepageUrl"],  # pyright: ignore[reportAny]
            license=data["licenseInfo"]["spdxId"],  # pyright: ignore[reportAny]
            stars=data["stargazerCount"],  # pyright: ignore[reportAny]
            topics=[
                node["topic"]["name"]
                for node in data["repositoryTopics"]["nodes"]  # pyright: ignore[reportAny]
            ],
            archived=data["isArchived"],  # pyright: ignore[reportAny]
            archived_at=datetime.fromisoformat(data["archivedAt"])  # pyright: ignore[reportAny]
            if data["archivedAt"] is not None
            else None,
        ),
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
        data = await response.json()  # pyright: ignore[reportAny]

        if not response.ok:
            logger.error(data)  # pyright: ignore[reportAny]
            response.raise_for_status()
            raise Exception()  # dead code

    new_owner, new_repo = data["owner"]["login"], data["name"]  # pyright: ignore[reportAny]
    if new_owner != owner:
        logger.warning(
            f"GH repository's ({owner}/{repo}) owner has changed to {new_owner}!"
        )
    if new_repo != repo:
        logger.warning(
            f"GH repository's ({owner}/{repo}) name has changed to {new_owner}!"
        )

    return GHRepository(
        owner=new_owner,  # pyright: ignore[reportAny]
        repo=new_repo,  # pyright: ignore[reportAny]
        branch=data["default_branch"],  # pyright: ignore[reportAny]
        commit=None,
        meta=MetaInformation(
            description=data["description"],  # pyright: ignore[reportAny]
            homepage=data["homepage"],  # pyright: ignore[reportAny]
            license=data["license"]["spdx_id"],  # pyright: ignore[reportAny]
            stars=data["stargazers_count"],  # pyright: ignore[reportAny]
            topics=data["topics"],  # pyright: ignore[reportAny]
            archived=data["archived"],  # pyright: ignore[reportAny]
            # this may not be always accurate, but it is the closest
            # we can get using REST API. Next time someone will use
            # GraphQL on this repo, it will pick the correct date
            archived_at=datetime.fromisoformat(data["updated_at"])  # pyright: ignore[reportAny]
            if data["archived"]
            else None,
        ),
    )
