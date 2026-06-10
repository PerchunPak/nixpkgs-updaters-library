Advanced features
=================

Auto-commit
-----------

The library can implement automatic commits with proper messages on every entry
addition/update. It is enough to just implement these three methods:

.. code:: python

   @dataclasses.dataclass
   class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
       # ...

       def gen_autocommit_message_add(self, entry: MyEntry) -> str:
           """Generate commit message, when user adds a new entry."""
           return f"somePlugins.{entry.info.id}: init at {entry.version}"

       def gen_autocommit_message_update_one(
           self,
           old_entry: MyMiniEntry,
           new_entry: MyEntry,
       ) -> str:
           """Generate commit message, when user updates one entry."""
           return f"somePlugins.{new_entry.info.id}: {old_entry.version} -> {new_entry.version}"

       def gen_autocommit_message_update_all(self, /) -> str:
           """Generate commit message, when user updates all entries."""
           return f"somePlugins: update on {date.today()}"

Implementing these three methods will allow the usage of the ``--autocommit``
CLI option. The library creates one commit per every entry added/updated,
unless user asks to update all entries.
