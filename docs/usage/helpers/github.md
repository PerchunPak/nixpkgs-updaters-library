# GitHub repository fetcher

This helper implements extensive fetching for GitHub repositories.

!!! info

    All requests to the functions are automatically cached.

## Fetching general information about GitHub repository

If you have a GitHub API token, you should use
[`github_fetch_graphql`][nupd.fetchers.github.github_fetch_graphql], if you
don't - [`github_fetch_rest`][nupd.fetchers.github.github_fetch_rest].

The difference, is that GraphQL requires API key, but has much higher rate
limits, while REST API is the opposite. Which makes REST API great for one-time
uses and GraphQL for massive updates.

After you fetched general information about the repository, you would probably
want to fetch such things as latest commit/release/Git tag. For this you should
use [`result.prefetch_commit()`][nupd.fetchers.github.GHRepository.prefetch_commit]
and/or [`result.prefetch_latest_version()`][nupd.fetchers.github.GHRepository.prefetch_latest_version].
As every function is limited to only one request (this is to make predicting
rate limiting intuitive), [`github_fetch_rest`][nupd.fetchers.github.github_fetch_rest]
will not fetch that data but [`github_fetch_graphql`][nupd.fetchers.github.github_fetch_graphql]
will (GraphQL allows us to include multiple requests into one).

!!! note

    Those functions don't do any additional requests if data is already present
    in the result object. Which means, you can safely do code like this:

    ```py
    if token:
        result = await github_fetch_graphql(...)
    else:
        result = await github_fetch_rest(...)

    # if we used GraphQL API, we already have that data,
    # so these functions return immediately
    result = await result.prefetch_commit()
    result = await result.prefetch_latest_version()
    ```

Don't forget to consult [`result.prefetch_commit()`][nupd.fetchers.github.GHRepository.prefetch_commit]
and [`result.prefetch_latest_version()`][nupd.fetchers.github.GHRepository.prefetch_latest_version].

## Functions

::: nupd.fetchers.github.github_fetch_graphql

::: nupd.fetchers.github.github_fetch_rest

!!! warning

    Other undocumented functions in this module are considered private and you
    should not use them.

## Response classes

::: nupd.fetchers.github.GHRepository
    options:
      filters:
      - "!get_prefetch_url"

::: nupd.fetchers.github.MetaInformation

::: nupd.fetchers.github.Commit
