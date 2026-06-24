``nix-prefetch-url`` wrapper
============================

See also documentation for `nix-prefetch-url <https://nix.dev/manual/nix/latest/command-ref/nix-prefetch-url>`_.

.. note::

    All requests to the functions are automatically cached.

.. autofunction:: nupd.fetchers.nix_prefetch_url.prefetch_url

.. autofunction:: nupd.fetchers.nix_prefetch_url.prefetch_obj

Response classes
----------------

.. autoclass:: nupd.fetchers.nix_prefetch_url.URLPrefetchResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.fetchers.nix_prefetch_url.URLPrefetchError
   :members:
   :undoc-members:
   :show-inheritance:
