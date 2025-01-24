import typing as t
from datetime import datetime

import aiohttp
import attrs
import inject
from attrs import define, field
from loguru import logger

from nupd.cache import Cache
from nupd.exc import HTTPError
from nupd.utils import json_serialize, json_transformer


@define(frozen=True, field_transformer=json_transformer)
class MetaInformation:
    description: str | None
    homepage: str | None
    license: str | None
    stars: int
    archived: bool
    archived_at: datetime | None


@define(frozen=True, field_transformer=json_transformer)
class Commit:
    id: str
    date: datetime


@define(frozen=True)
class GHRepository:
    owner: str
    repo: str
    branch: str

    commit: Commit | None = field(
        converter=lambda x: Commit(**x)
        if not isinstance(x, Commit | None)
        else x
    )
    meta: MetaInformation = field(
        converter=lambda x: MetaInformation(**x)
        if not isinstance(x, MetaInformation)
        else x
    )

    async def prefetch_commit(
        self, *, github_token: str | None = None
    ) -> t.Self:
        commit = await github_prefetch_commit(self, github_token=github_token)
        return attrs.evolve(self, commit=commit)

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"

    def get_prefetch_url(self) -> str:
        if self.commit is None:
            raise ValueError(
                "To get archive URL, you have to prefetch commit first"
            )
        return f"{self.url}/archive/{self.commit}.tar.gz"


async def github_fetch_graphql(
    owner: str, repo: str, github_token: str
) -> GHRepository:
    cache = inject.instance(Cache)["github_fetch"]
    try:
        return GHRepository(**await cache.get(f"{owner}/{repo}"))  # pyright: ignore[reportCallIssue]
    except KeyError:
        result = await _github_fetch_graphql(owner, repo, github_token)
        await cache.set(
            f"{owner}/{repo}",
            attrs.asdict(result, value_serializer=json_serialize),
        )
        return result


async def _github_fetch_graphql(
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
                "        ... on Commit {"
                "          committedDate"
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
            raise RuntimeError("dead code")  # pragma: no cover
        if data.get("errors"):
            logger.error(data)
            raise HTTPError(
                "\n".join(error["message"] for error in data["errors"])
            )

    logger.debug(
        f"Fetching GH:{owner}/{repo} took {data["data"]["rateLimit"]["cost"]} point(s)"
    )
    data = data["data"]["repository"]

    if not (
        commit_date := data["defaultBranchRef"]["target"].get("committedDate")
    ):
        raise RuntimeError(
            "You've encountered a weird edge-case. Please open a bug report"
        )

    return GHRepository(
        owner=data["owner"]["login"],
        repo=data["name"],
        branch=data["defaultBranchRef"]["name"],
        commit=Commit(
            id=data["defaultBranchRef"]["target"]["oid"],
            date=commit_date,
        ),
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


async def github_fetch_rest(
    owner: str, repo: str, *, github_token: str | None
) -> GHRepository:
    cache = inject.instance(Cache)["github_fetch"]
    try:
        return GHRepository(**await cache.get(f"{owner}/{repo}"))  # pyright: ignore[reportCallIssue]
    except KeyError:
        result = await _github_fetch_rest(
            owner, repo, github_token=github_token
        )
        await cache.set(
            f"{owner}/{repo}",
            attrs.asdict(result, value_serializer=json_serialize),
        )
        return result


async def _github_fetch_rest(
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


async def github_prefetch_commit(
    repo: GHRepository, *, github_token: str | None
) -> Commit:
    cache = inject.instance(Cache)["github_commit_prefetch"]
    try:
        return Commit(
            **t.cast(
                dict[str, t.Any], await cache.get(repo.url + "@" + repo.branch)
            )
        )
    except KeyError:
        result = await _github_prefetch_commit(repo, github_token=github_token)
        await cache.set(
            repo.url, attrs.asdict(result, value_serializer=json_serialize)
        )
        return result


async def _github_prefetch_commit(
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
