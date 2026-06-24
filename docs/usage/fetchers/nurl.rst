``nurl`` wrapper
================

`nurl`_ is a simple tool, that can prefetch all imaginable sources with ease.

.. warning::

   Nurl uses ``nix flake prefetch`` which often fails under high workload.
   Prefer to use other fetchers or retry this function in case of a failure.
   Error might look like this:

   .. code:: bash

      $ nix flake prefetch --extra-experimental-features 'nix-command flakes' --json github:kristijanhusak/vim-dadbod-ui/07e92e22114cc5b1ba4938d99897d85b58e20475
      unpacking 'github:kristijanhusak/vim-dadbod-ui/07e92e22114cc5b1ba4938d99897d85b58e20475' into the Git cache...
      error:
             … while fetching the input 'github:kristijanhusak/vim-dadbod-ui/07e92e22114cc5b1ba4938d99897d85b58e20475'

             error: adding a file to a tree builder: failed to insert entry: invalid object specified - LICENSE (libgit2 error code = 14)
      Error: command exited with exit status: 1

      Location:
          src/prefetch.rs:22:13


.. note::

    All requests to the functions are automatically cached.

Functions
---------

.. autofunction:: nupd.fetchers.nurl.nurl

.. autofunction:: nupd.fetchers.nurl.nurl_parse

Response classes
----------------

``FETCHERS`` is a list of all fetchers that ``nurl`` supports (obtained via
``nurl -l``).

.. autoclass:: nupd.fetchers.nurl.NurlResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.fetchers.nurl.NurlError
   :members:
   :undoc-members:
   :show-inheritance:



.. _nurl: https://github.com/nix-community/nurl
