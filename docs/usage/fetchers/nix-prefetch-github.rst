``nix-prefetch-github`` wrapper
===============================

`nix-prefetch-github <https://github.com/seppeljordan/nix-prefetch-github>`_ is
a project specifically for prefetching GitHub repositories.

.. code-block::

  $ nix-prefetch-github --help
  usage: nix-prefetch-github [-h] [--fetch-submodules] [--no-fetch-submodules]
                             [--leave-dot-git] [--no-leave-dot-git]
                             [--deep-clone] [--no-deep-clone] [--verbose]
                             [--quiet] [--nix] [--json] [--meta] [--version]
                             [--rev REV]
                             owner repo

  positional arguments:
    owner
    repo

  options:
    -h, --help            show this help message and exit
    --fetch-submodules    Include git submodules in the output derivation
    --no-fetch-submodules
                          Don't include git submodules in output derivation
    --leave-dot-git       Include .git folder in output derivation. Use this if
                          you need repository data, e.g. current commit hash,
                          for the build process.
    --no-leave-dot-git    Don't include .git folder in output derivation.
    --deep-clone          Include all of the repository history in the output
                          derivation. This option implies --leave-dot-git.
    --no-deep-clone       Don't include the repository history in the output
                          derivation.
    --verbose, -v         Print additional information about the programs
                          execution. This is useful if you want to issue a bug
                          report.
    --quiet, -q           Print less information about the programs execution.
    --nix                 Output the results as valid nix code.
    --json                Output the results in the JSON format
    --meta                Output the results in JSON format where the arguments
                          to fetchFromGitHub are located under the src key of
                          the resulting json dictionary and meta information
                          about the prefetched repository is located under the
                          meta key of the output.
    --version             show program's version number and exit
    --rev REV


.. note::

    All requests to the functions are automatically cached.

.. autofunction:: nupd.fetchers.nix_prefetch_github.prefetch_github

Response classes
----------------

.. autoclass:: nupd.fetchers.nix_prefetch_github.GithubPrefetchResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.fetchers.nix_prefetch_github.GithubPrefetchError
   :members:
   :undoc-members:
   :show-inheritance:
