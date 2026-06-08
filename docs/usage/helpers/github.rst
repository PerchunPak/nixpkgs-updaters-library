GitHub repository fetcher
=========================

This helper implements extensive fetching for GitHub repositories.

.. note::

    All requests to the functions are automatically cached.

Fetching general information about GitHub repository
----------------------------------------------------

If you have a GitHub API token, you should use :func:`.github_fetch_graphql`,
if you don't - :func:`.github_fetch_rest`.

The difference, is that GraphQL requires API key, but has much higher rate
limits, while REST API is the opposite. Which makes REST API great for one-time
uses and GraphQL for massive updates.

After you fetched general information about the repository, you would probably
want to fetch such things as latest commit/release/Git tag. For this you should
use :meth:`.prefetch_commit` and/or :meth:`.prefetch_latest_version`. As every
function is limited to only one request (this is to make predicting rate
limiting intuitive), :func:`.github_fetch_rest` will not fetch that data but
:func:`.github_fetch_graphql` will (GraphQL allows us to include multiple
requests into one).

.. note::

    Those functions don't do any additional requests if data is already present
    in the result object. Which means, you can safely do like this:

    .. code-block:: python

      if token:
          result = await github_fetch_graphql(...)
      else:
          result = await github_fetch_rest(...)

      # if we used GraphQL API, we already have that data,
      # so these functions return immediately
      result = await result.prefetch_commit()
      result = await result.prefetch_latest_version()

Don't forget to consult
:meth:`result.prefetch_commit() <.GHRepository.prefetch_commit>`
and :meth:`result.prefetch_latest_version() <.GHRepository.prefetch_latest_version>`.

Functions
---------

.. warning::

    Other undocumented functions in this module are considered private and you
    should not use them.

.. autofunction:: nupd.fetchers.github.github_fetch_graphql

.. autofunction:: nupd.fetchers.github.github_fetch_rest

Response classes
----------------

.. autoclass:: nupd.fetchers.github.GHRepository
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: model_config,get_prefetch_url

.. autoclass:: nupd.fetchers.github.MetaInformation
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.fetchers.github.Commit
   :members:
   :undoc-members:
   :show-inheritance:
