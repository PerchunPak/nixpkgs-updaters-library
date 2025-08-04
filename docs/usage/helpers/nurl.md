# `nurl` wrapper

`nurl` is THE prefetcher, that can prefetch all imaginable sources with ease.
You should always prefer it over other fetchers (only for prefetching the
hash, it can't do the job of the [GitHub helper](./github.md) for example).

!!! info

    All requests to the functions are automatically cached.

## Fetching general information about GitHub repository

If you have a GitHub API token, you should use
[`github_fetch_graphql`][nupd.fetchers.github.github_fetch_graphql], if you
don't - [`github_fetch_rest`][nupd.fetchers.github.github_fetch_rest].

The difference, is that GraphQL requires API key, but has much higher rate
limits, while REST API is the opposite. Which makes REST API great for one-time
usecase and GraphQL for massive updates.

After you fetched general information about the repository, you would probably
want to fetch such things as latest commit/release/Git tag. For this you should
use [`result.prefetch_commit()`][nupd.fetchers.github.GHRepository.prefetch_commit]
and/or [`result.prefetch_latest_version()`][nupd.fetchers.github.GHRepository.prefetch_latest_version].
As every function is limited to only one request (this is to make predicting
rate limiting intuitive), [`github_fetch_rest`][nupd.fetchers.github.github_fetch_rest]
will not fetch that data but [`github_fetch_graphql`][nupd.fetchers.github.github_fetch_graphql]
will.

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

::: nupd.fetchers.nurl.nurl
    options:
      find_stubs_package: true
      force_inspection: true

::: nupd.fetchers.nurl.nurl_parse

## Response classes

`FETCHERS` is a list of all fetchers that `nurl` supports (obtained via `nurl -l`).

::: nupd.fetchers.nurl.NurlResult

::: nupd.fetchers.nurl.NurlError
