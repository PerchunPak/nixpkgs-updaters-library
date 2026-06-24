``nix-prefetch-git`` wrapper
============================

``nix-prefetch-git`` is a script, that exists purely inside nixpkgs. You can read
its source code `here`_ (`permalink`_) or read its `--help` on the moment of
the writing:

.. _here: https://github.com/NixOS/nixpkgs/blob/master/pkgs/build-support/fetchgit/nix-prefetch-git
.. _permalink: https://github.com/NixOS/nixpkgs/blob/7cbb56ffe0298a6d55233b9ccb857eff3e65509d/pkgs/build-support/fetchgit/nix-prefetch-git

.. code-block::

  $ nix-prefetch-git --help
  syntax: nix-prefetch-git [options] [URL [REVISION [EXPECTED-HASH]]]

  Options:
        --out path      Path where the output would be stored.
        --url url       Any url understood by 'git clone'.
        --rev ref       Any sha1 or references (such as refs/heads/master)
        --hash h        Expected hash.
        --name n        Symbolic store path name to use for the result (default: based on URL)
        --branch-name   Branch name to check out into
        --sparse-checkout Only fetch and checkout part of the repository.
        --non-cone-mode Use non-cone mode for sparse checkouts.
        --deepClone     Clone the entire repository.
        --no-deepClone  Make a shallow clone of just the required ref.
        --leave-dotGit  Keep the .git directories.
        --fetch-lfs     Fetch git Large File Storage (LFS) files.
        --fetch-submodules Fetch submodules.
        --fetch-tags    Fetch all tags (useful for git describe).
        --builder       Clone as fetchgit does, but url, rev, and out option are mandatory.
        --no-add-path   Do not actually add the contents of the git repo to the store.
        --root-dir dir  Directory in the repository that will be copied to the output instead of the full repository.
        --quiet         Only print the final json summary.

.. note::

    All requests to the functions are automatically cached.

.. autofunction:: nupd.fetchers.nix_prefetch_git.prefetch_git

Response classes
----------------

.. autoclass:: nupd.fetchers.nix_prefetch_git.GitPrefetchResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.fetchers.nix_prefetch_git.GitPrefetchError
   :members:
   :undoc-members:
   :show-inheritance:
