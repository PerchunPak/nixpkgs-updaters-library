Quick Start
===========

Let's together create a simple example script, that loads GitHub URLs from an
``input.csv`` file, and outputs last commit and hashes to an ``output.json``
file.

You can view the full code in the `example/simple`_ directory.

.. _example/simple: https://github.com/PerchunPak/nixpkgs-updaters-library/tree/main/example/simple

First, we need to implement :doc:`our models </usage/models>`.

.. code-block:: python

  from __future__ import annotations

  from nupd.models import EntryInfo, Entry
  from nupd.fetchers.github import GHRepository
  from nupd.fetchers.nurl import NurlResult


  class MyEntryInfo(EntryInfo, frozen=True):
      owner: str
      repo: str

      # This is a property because we could, for example, implement aliases.
      @property
      def id(self) -> str:
          return self.repo

  class MyEntry(Entry[EntryInfo, MyMiniEntry], frozen=True):
      info: MyEntryInfo
      fetched: GHRepository
      nurl_result: NurlResult

Wait, what is :class:`.GHRepository` and :class:`.NurlResult`? Nupd
implements a bunch of helpers for you. This includes an :doc:`easy fetcher for
GitHub repositories <./helpers/github>` and `a wrapper <./helpers/nurl>`_
around `nurl <https://github.com/nix-community/nurl>`_ - THE prefetcher for Nix
ecosystem.

Next, let's implement :func:`MyEntryInfo.fetch <.EntryInfo>`:

.. code-block:: python

  class MyEntryInfo(EntryInfo, frozen=True):
      # ...

      async def fetch(self) -> MyEntry:
          logger.debug(f"Fetching {self.owner}/{self.repo}")

          result = await github_fetch_rest(
              self.owner, self.repo, github_token=None
          )

          # fetch latest commit info
          result = await result.prefetch_commit()
          # and latest tag version
          result = await result.prefetch_latest_version()
          # then run nurl to generate `fetchFromGitHub`
          prefetched = await nurl.nurl(
              result.url, submodules=bool(result.has_submodules)
          )

          return MyEntry(info=self, fetched=result, nurl_result=prefetched)

We should also implement :class:`.MiniEntry`, which is just a minified version
of our :class:`.Entry` so we won't bloat the result file with unnecessary
information:

.. code-block:: python

  class MyEntry:
      # ...

      @t.override
      def minify(self) -> MyMiniEntry:
          return MyMiniEntry(
              info=self.info,
              nurl=self.nurl_result,
          )

  class MyMiniEntry(MiniEntry[MyEntryInfo], frozen=True):
      # this class will automatically include an `info` field, which points to
      # `EntryInfo`
      nurl: nurl.NurlResult

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
  2026-06-07 14:31:11.455 | DEBUG    | nupd.logs:setup_logging:52 - Logging was setup!
  2026-06-07 14:31:11.456 | INFO     | nupd.base:fetch_entries:159 - Going to fetch 3 entries with the limit of 32 simultaneously
  2026-06-07 14:31:11.456 | DEBUG    | __main__:fetch:39 - Fetching nvim-treesitter/nvim-treesitter
  2026-06-07 14:31:11.460 | DEBUG    | __main__:fetch:39 - Fetching folke/todo-comments.nvim
  2026-06-07 14:31:11.461 | DEBUG    | __main__:fetch:39 - Fetching tpope/vim-surround
  2026-06-07 14:31:12.262 | DEBUG    | nupd.fetchers.nurl:nurl:69 - Running nurl on https://github.com/folke/todo-comments.nvim
  2026-06-07 14:31:12.433 | DEBUG    | nupd.fetchers.nurl:nurl:69 - Running nurl on https://github.com/tpope/vim-surround
  2026-06-07 14:31:12.586 | DEBUG    | nupd.fetchers.nurl:nurl:69 - Running nurl on https://github.com/nvim-treesitter/nvim-treesitter
  2026-06-07 14:31:12.719 | SUCCESS  | nupd.base:update_cmd:149 - Successfully updated 3 entries!

It is that simple! Now, let's check out our ``output.json``:

.. code-block:: json
   :caption: output.json

   {
     "nvim-treesitter": {
       "info": {
         "owner": "nvim-treesitter",
         "repo": "nvim-treesitter"
       },
       "nurl": {
         "args": {
           "hash": "sha256-ZQ3HJ3dhtMS75GpW9xxt/ERjqD6v/Fzw+NLyml2EuYM=",
           "owner": "nvim-treesitter",
           "repo": "nvim-treesitter",
           "rev": "c1efc9a9058bb54cfcb6f0a4fc14a4ac8a66bdaa"
         },
         "fetcher": "fetchFromGitHub"
       }
     },
     "todo-comments.nvim": {
       "info": {
         "owner": "folke",
         "repo": "todo-comments.nvim"
       },
       "nurl": {
         "args": {
           "hash": "sha256-at9OSBtQqyiDdxKdNn2x6z4k8xrDD90sACKEK7uKNUM=",
           "owner": "folke",
           "repo": "todo-comments.nvim",
           "rev": "304a8d204ee787d2544d8bc23cd38d2f929e7cc5"
         },
         "fetcher": "fetchFromGitHub"
       }
     },
     "vim-surround": {
       "info": {
         "owner": "tpope",
         "repo": "vim-surround"
       },
       "nurl": {
         "args": {
           "hash": "sha256-DZE5tkmnT+lAvx/RQHaDEgEJXRKsy56KJY919xiH1lE=",
           "owner": "tpope",
           "repo": "vim-surround",
           "rev": "3d188ed2113431cf8dac77be61b842acb64433d9"
         },
         "fetcher": "fetchFromGitHub"
       }
     }
   }
