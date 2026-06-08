Models
======

You need to implement some interfaces for the library to work. Note that the
library is generally designed to be minimalistic: you choose what to store.
This way, the library can be used for anything from simple git repositories to
GNOME extensions.

Look at `the models.py file <https://github.com/PerchunPak/nixpkgs-updaters-library/blob/main/nupd/models.py>`_
for the exact details.

.. autoclass:: nupd.models.NupdModel

.. autoclass:: nupd.models.EntryInfo
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.models.Entry
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nupd.models.MiniEntry
   :members:
   :undoc-members:
   :show-inheritance:
