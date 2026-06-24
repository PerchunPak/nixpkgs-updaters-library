Recipes
=======

Recipes are ready-to-go implementation of most use-cases. They implement the
common wiring of different fetch methods and return complete objects, that can
be parsed by Nix (e.g. fetcher arguments).

Currently, recipes are implemented only for
:doc:`GitHub repositories </usage/fetchers/github>`
and :doc:`nix-prefetch-git </usage/fetchers/nix-prefetch-git>`.

``nix-prefetch-git`` recipy
---------------------------

This is the recipy for generic Git repositories. Compared to :func:`.prefetch_git`,
this can automatically generate Nix-formatted version and optionally pin to
tags. Example:

.. code-block:: python

   from nupd.fetchers.nix_prefetch_git import GitRecipy

   print(await GitRecipy.fetch("PerchunPak", "ghcherry"))
   # outputs
   GitRecipy(
       version="1.6.0-unstable-2026-06-23",
       fetcher="fetchgit",
       fetcher_args={
           "url": "https://github.com/PerchunPak/ghcherry",
           "rev": "cd849e8c9017ab74f12b19f98656dd1b7973658b",
           "hash": "sha256-2XLJxmqZDJyzJbikGEc0rrj7r5ChBhMt45Y67zijY4s=",
       },
       meta=NixMetaInformation(),
       prefetched=GitPrefetchResult(
           url="https://github.com/PerchunPak/ghcherry",
           rev="cd849e8c9017ab74f12b19f98656dd1b7973658b",
           date=datetime.datetime("2026-06-23 05:56:06", tzinfo=TzInfo(0)),
           path="/nix/store/f2hdf84f3l2qg1wkn8zh6ngrxpxc8imw-ghcherry",
           hash="sha256-2XLJxmqZDJyzJbikGEc0rrj7r5ChBhMt45Y67zijY4s=",
           fetch_lfs=False,
           fetch_submodules=False,
           deep_clone=False,
           leave_dot_git=False,
       ),
   )

.. autoclass:: nupd.fetchers.nix_prefetch_git.GitRecipy
   :members:
   :undoc-members:
   :show-inheritance:

.. _github-recipy:

GitHub recipy
-------------

.. code-block:: python

   from nupd.fetchers.github import GithubRecipy

   print(await GithubRecipy.fetch("PerchunPak", "ghcherry"))
   # outputs
   GithubRecipy(
       version="1.6.0-unstable-2026-06-23",
       fetcher="fetchFromGitHub",
       fetcher_args={
           "owner": "PerchunPak",
           "repo": "ghcherry",
           "hash": "sha256-2XLJxmqZDJyzJbikGEc0rrj7r5ChBhMt45Y67zijY4s=",
           "rev": "cd849e8c9017ab74f12b19f98656dd1b7973658b",
       },
       meta=NixMetaInformation(
           description="Cherry-pick commits across GitHub repositories using only the GitHub API",
           license="Apache-2.0",
       ),
       fetched_repo=GHRepository(  # excluded when generating JSON
           owner="PerchunPak",
           repo="ghcherry",
           branch="main",
           meta=MetaInformation(
               description="Cherry-pick commits across GitHub repositories using only the GitHub API",
               homepage=None,
               license="Apache-2.0",
               stars=5,
               archived=False,
               archived_at=None,
           ),
           has_submodules=False,
           commit=Commit(
               id="cd849e8c9017ab74f12b19f98656dd1b7973658b",
               date=datetime.datetime("2026-06-23 05:56:06", tzinfo=TzInfo(0)),
           ),
           latest_version="v1.6.0",
       ),
       prefetched=GithubPrefetchResult(  # excluded when generating JSON
           owner="PerchunPak",
           repo="ghcherry",
           rev="cd849e8c9017ab74f12b19f98656dd1b7973658b",
           hash="sha256-2XLJxmqZDJyzJbikGEc0rrj7r5ChBhMt45Y67zijY4s=",
           commit_date=None,
           fetch_submodules=False,
           leave_dot_git=False,
           deep_clone=False,
       ),
   )

.. autoclass:: nupd.fetchers.github.GithubRecipy
   :members:
   :undoc-members:
   :show-inheritance:

These are the functions, that you can pass to :meth:`.GithubRecipy.fetch` as
the ``versioning_strategy`` argument:

.. autofunction:: nupd.fetchers.github.version_by_tag

.. autofunction:: nupd.fetchers.github.version_by_commit

.. autoclass:: nupd.fetchers.github.ResolvedVersion
   :members:
   :undoc-members:
   :show-inheritance:

Base classes
------------

.. autoclass:: nupd.helpers.recipy.ABCRecipy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.helpers.recipy.NixMetaInformation
   :members:
   :undoc-members:
   :show-inheritance:
