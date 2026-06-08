``nurl`` wrapper
================

`nurl`_ is THE prefetcher, that can prefetch all imaginable sources with ease.
You should always prefer it over other fetchers (only for prefetching the hash,
it can't do the job of the :doc:`GitHub helper <github>` for
example).

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
