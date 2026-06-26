Quick Start
===========

Let's together create a simple example script, that loads Git repositories from
an ``input.csv`` file, and outputs last commit and hashes to an ``output.json``
file.

You can view the full code in the `example/simple`_ directory.

.. _example/simple: https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple

First, we need to implement :doc:`our models </usage/models>`.

.. code-block:: python

  from __future__ import annotations

  from nupd.fetchers.github import GithubRecipy
  from nupd.models import EntryInfo, Entry


  class MyEntryInfo(EntryInfo, frozen=True):
      owner: str
      repo: str

      # This is a property because we could, for example, implement aliases.
      @property
      def id(self) -> str:
          return self.repo

  class MyEntry(Entry[EntryInfo, MyMiniEntry], frozen=True):
      info: MyEntryInfo
      fetched: GithubRecipy

Wait, what is :class:`.GithubRecipy`? Nupd implements a bunch of helpers for
you. This includes an :ref:`easy recipy-fetcher for GitHub repositories
<github-recipy>`.

Next, let's implement :func:`MyEntryInfo.fetch <nupd.models.EntryInfo>`:

.. code-block:: python

  class MyEntryInfo(EntryInfo, frozen=True):
      # ...

      async def fetch(self) -> MyEntry:
          logger.debug(f"Fetching {self.owner}/{self.repo}")

          # fetch all possible information about the entry
          # this will also automatically use GitHub token from the `GITHUB_TOKEN`
          # environment variable
          result = await GithubRecipy.fetch(self.owner, self.repo)

          # NOTE: We could also handle redirects like this
          if (self.owner, self.repo) != (
              result.fetched_repo.owner,
              result.fetched_repo.repo,
          ):
              ...

          return MyEntry(info=self, fetched=result)

We should also implement :class:`.MiniEntry`, which is just a minified version
of our :class:`.Entry` so we won't bloat the result file with unnecessary
information:

.. code-block:: python

  from nupd.utils import FrozenDict

  class MyEntry:
      # ...

      def minify(self) -> MyMiniEntry:
          return MyMiniEntry(
              info=self.info,
              version=self.fetched.version,
              fetcher=self.fetched.fetcher,
              fetcher_args=self.fetched.fetcher_args,
              meta=self.fetched.meta,
          )

  class MyMiniEntry(MiniEntry[MyEntryInfo], frozen=True):
      # this class will automatically include an `info` field, which points to `EntryInfo`
      version: str
      fetcher: str
      fetcher_args: FrozenDict[str, t.Any]
      meta: NixMetaInformation | None

Implement core logic
--------------------

.. code-block:: python

  import collections.abc as c
  import dataclasses
  import typing as t
  from pathlib import Path

  from nupd.base import ABCBase

  ROOT = Path(__file__).parent
  if "/nix/store" in str(ROOT):
      # we are bundled using nix, use working directory instead of root
      ROOT = Path.cwd()


  @dataclasses.dataclass
  class MyImpl(ABCBase[MyEntry, MyEntryInfo]):
      # Due to some implementation details, we cannot provide custom arguments
      # definitions for existing commands (however you can implement new
      # commands!), we have to provide default values for input and output files
      # this way.
      _default_input_file: Path = dataclasses.field(
          init=False, default=ROOT / "input.csv"# (1)!
      )
      # If you want to provide a path to nixpkgs, you can do so using
      # `nupd.utils.NIXPKGS_PLACEHOLDER / "your" / "path" / "file.csv"`. This
      # will automatically use the nixpkgs path provided in CLI the flag.
      _default_output_file: Path = dataclasses.field(
          init=False, default=ROOT / "output.json"
      )


In this class, we only have to implement 3 methods to get access to all features:

.. autoclass:: nupd.base.ABCBase.get_all_entries

.. code-block:: python

    async def get_all_entries(self) -> c.Iterable[MyEntryInfo]:
        """Get all entries from the `input.csv` file."""
        return CsvInput(self.input_file).read(
            lambda x: MyEntryInfo(**x)
        )

Note that this method is async, so you can implement reading a list of packages
as an HTTP request to central package distribution center (e.g. PyPi).

.. autofunction:: nupd.base.ABCBase.write_entries_info

Save basic information about our entries.

.. code-block:: python

  def write_entries_info(self, entries_info: c.Iterable[MyEntryInfo]) -> None:
      """Save the result to `input.csv`."""
      CsvInput(self.input_file).write(
          entries_info,
          serialize=lambda x: x.model_dump(mode="json"),
      )

.. autofunction:: nupd.base.ABCBase.parse_entry_id

.. code-block:: python

   def parse_entry_id(self, to_parse: str) -> MyEntryInfo:
       """Parse CLI argument to `EntryInfo`.

       Example:
           If user runs `$ python script.py add foo/bar`,
           we will get the `foo/bar` part to parse.
       """
       split = to_parse.split("/")
       if len(split) != 2:
           raise InvalidArgumentError(
               f"Invalid value passed: {to_parse!r}. "
               "Should be something like 'owner/repo'"
           )

       owner, repo = split
       return MyEntryInfo(owner=owner, repo=repo)

Boilerplate
-----------

At last, we have to write some amount of boilerplate:

.. code-block:: python

  from nupd.utils import register_implementation_classes

  if __name__ == "__main__":
      # this is how we point out which implementation classes we use
      register_implementation_classes(
          ImplClasses(
              base=MyImpl,
              mini_entry=MyMiniEntry,
              entry=MyEntry,
              entry_info=MyEntryInfo,
          )
      )

      app.meta()

Let's run the actual script
---------------------------

You can view the full script
`here <https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple>`_.
But before running it, we have to create ``input.csv``:

.. code-block::
   :caption: input.csv

   owner,repo
   nvim-treesitter,nvim-treesitter
   folke,todo-comments.nvim
   tpope,vim-surround

And, finally, let's run the script!

.. code-block::

  $ python script.py --log-level debug update
  2026-06-24 14:41:08.607 | DEBUG    | nupd.logs:setup_logging:40 - Logging was setup!
  2026-06-24 14:41:08.612 | INFO     | nupd.base:fetch_entries:314 - Going to fetch 3 entries with the limit of 20 simultaneously
  2026-06-24 14:41:08.614 | DEBUG    | __main__:fetch:43 - Fetching nvim-treesitter/nvim-treesitter
  2026-06-24 14:41:08.635 | DEBUG    | __main__:fetch:43 - Fetching folke/todo-comments.nvim
  2026-06-24 14:41:08.650 | DEBUG    | __main__:fetch:43 - Fetching tpope/vim-surround
  2026-06-24 14:41:08.669 | SUCCESS  | nupd.base:update_cmd:251 - Successfully fetched 3 entries!
  2026-06-24 14:41:08.670 | SUCCESS  | nupd.base:update_cmd:304 - Successfully updated 3 entries!

It is that simple! Now, let's check out our ``output.json``:

.. code-block:: json
   :caption: output.json

   {
     "nvim-treesitter": {
       "fetcher": "fetchFromGitHub",
       "fetcher_args": {
         "hash": "sha256-PQR6tFt4lCrAZNQG7BLMD1IiCKja9wDS1S4laGJf/HE=",
         "owner": "nvim-treesitter",
         "repo": "nvim-treesitter",
         "rev": "4916d6592ede8c07973490d9322f187e07dfefac"
       },
       "info": {
         "owner": "nvim-treesitter",
         "repo": "nvim-treesitter"
       },
       "meta": {
         "description": "Nvim Treesitter configurations and abstraction layer",
         "license": "Apache-2.0"
       },
       "version": "0.10.0-unstable-2026-04-03"
     },
     "todo-comments.nvim": {
       "fetcher": "fetchFromGitHub",
       "fetcher_args": {
         "hash": "sha256-VGeIRfwQsHgSO89Pmn6yIP9na1F6mmYZx0HDLe9IKCQ=",
         "owner": "folke",
         "repo": "todo-comments.nvim",
         "rev": "31e3c38ce9b29781e4422fc0322eb0a21f4e8668"
       },
       "info": {
         "owner": "folke",
         "repo": "todo-comments.nvim"
       },
       "meta": {
         "description": "\u2705  Highlight, list and search todo comments in your projects",
         "license": "Apache-2.0"
       },
       "version": "1.5.0-unstable-2025-11-10"
     },
     "vim-surround": {
       "fetcher": "fetchFromGitHub",
       "fetcher_args": {
         "hash": "sha256-DZE5tkmnT+lAvx/RQHaDEgEJXRKsy56KJY919xiH1lE=",
         "owner": "tpope",
         "repo": "vim-surround",
         "rev": "3d188ed2113431cf8dac77be61b842acb64433d9"
       },
       "info": {
         "owner": "tpope",
         "repo": "vim-surround"
       },
       "meta": {
         "description": "Surround.vim: Delete/change/add parentheses/quotes/XML-tags/much more with ease",
         "homepage": "https://www.vim.org/scripts/script.php?script_id=1697"
       },
       "version": "2.2-unstable-2022-10-25"
     }
   }
