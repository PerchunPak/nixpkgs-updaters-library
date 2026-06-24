GitHub repository fetcher
=========================

This helper implements extensive fetching for GitHub repositories.

.. note::

    All requests to the functions are automatically cached.

Fetching general information about GitHub repository
----------------------------------------------------

There are four main methods to prefetch a GitHub repository:

- :func:`.github_fetch_rest`: Uses REST API to prefetch the repository. Token
  is optional, but rate limits are strict and not all information can be
  fetched in a single request.
- :func:`.github_fetch_graphql`: Uses GraphQL API, but requires a token. Has
  much bigger rate limits though, and allows to fetch all possible information
  in a single request.
- :func:`.github_fetch_auto`: Automatically chooses between GraphQL and REST
  APIs, based on whether ``GITHUB_TOKEN`` is present in environment variables.
- :func:`.github_full_fetch_auto`: The same as above, but does additional calls
  to fetch other optional information (only REST API can't fetch everything in
  one request).

After you fetched general information about the repository, you would probably
want to fetch such things as latest commit/release/Git tag. For this you should
use :meth:`.prefetch_commit` and/or :meth:`.prefetch_latest_version`. As every
function is limited to only one request (this is to make predicting rate
limiting intuitive), :func:`.github_fetch_rest` will not fetch that data but
:func:`.github_fetch_graphql` will (GraphQL allows us to include multiple
requests into one).

- :meth:`GHRepository.prefetch_commit`: Prefetch latest commit SHA and whether
  the repository has submodules.
- :meth:`GHRepository.prefetch_latest_version`: Prefetch latest version.

.. note::

    These functions don't do any additional requests if data is already present
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

Functions
---------

.. autofunction:: nupd.fetchers.github.github_fetch_auto

.. autofunction:: nupd.fetchers.github.github_full_fetch_auto

Low-level fetchers
^^^^^^^^^^^^^^^^^^

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
