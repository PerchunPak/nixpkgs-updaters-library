CSV Reader
==========

A simple helper to read and write CSV files.

Example
-------

.. code-block:: python

  from nupd.inputs.csv import CsvInput

  csv = CsvInput[MyEntryInfo]("input-file.csv")

  entry_infos = csv.read(lambda x: MyEntryInfo(**x))
  csv.write(entries_info, serialize=lambda x: x.model_dump(mode="json"))

API reference
-------------

.. autoclass:: nupd.inputs.csv.CsvInput
   :members:
   :undoc-members:
   :show-inheritance:
