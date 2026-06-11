# ruff: noqa: E101 # mixed indentation with tabs and spaces
import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nupd.base import Nupd
from nupd.models import ImplClasses
from tests.test_add_update_cmd.models import (
    DumbBaseAutocommit,
    DumbEntry,
    DumbEntryInfo,
    DumbMiniEntry,
)

from . import get_commits, prepare_test

UPDATE_ALL_PATCH = """\
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 {
 	"one": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
 			"name": "one"
 		},
 		"some_date": "1970-01-01T00:00:00Z"
 	},
 	"three": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
 			"name": "three"
 		},
 		"some_date": "1970-01-01T00:00:00Z"
 	},
 	"two": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
 			"name": "two"
 		},
"""
UPDATE_ONE_PATCH = """\
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 		"some_date": "1970-01-01T00:00:00Z"
 	},
 	"one": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
 			"name": "one"
 		},
"""
UPDATE_TWO_PATCH = """\
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 		"some_date": "1970-01-01T00:00:00Z"
 	},
 	"two": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
 			"extra": "extra",
 			"name": "two"
"""
UPDATE_THREE_PATCH = """\
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 		"some_date": "1970-01-01T00:00:00Z"
 	},
 	"three": {
-		"hash": "sha256-old/hash",
+		"hash": "sha256-some/cool/hash",
 		"info": {
-			"extra": "nice",
 			"name": "three"
 		},
 		"some_date": "1970-01-01T00:00:00Z"
"""


@pytest.mark.parametrize("autocommit", [False, True])
async def test_update_cmd_everything(
    tmp_path: Path, mocker: MockerFixture, autocommit: bool
) -> None:
    input_file, output_file = prepare_test(
        tmp_path,
        mocker,
        initial_entries={
            "one": DumbEntry(
                info=DumbEntryInfo(name="one"), hash="sha256-old/hash"
            ),
            "two": DumbEntry(
                info=DumbEntryInfo(name="two"), hash="sha256-old/hash"
            ),
            "three": DumbEntry(
                info=DumbEntryInfo(name="three"), hash="sha256-old/hash"
            ),
        },
        autocommit=autocommit,
    )

    # 2. add multiple plugins
    await Nupd(
        ImplClasses(
            mini_entry=DumbMiniEntry,
            base=DumbBaseAutocommit,
            entry=DumbEntry,
            entry_info=DumbEntryInfo,
        ),
    ).update_cmd(to_update=None, autocommit=autocommit)

    # 3. check the files content
    assert input_file.read_text() == "name,extra\none,\ntwo,\nthree,\n"
    assert json.loads(output_file.read_text()) == {
        "one": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "one"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "three": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "three"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "two": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "two"},
            "some_date": "1970-01-01T00:00:00Z",
        },
    }

    # 4. check commits
    if autocommit:
        assert get_commits(tmp_path) == [
            ("example: update all", UPDATE_ALL_PATCH),
        ]


@pytest.mark.parametrize("autocommit", [False, True])
async def test_update_cmd_specific(
    tmp_path: Path, mocker: MockerFixture, autocommit: bool
) -> None:
    input_file, output_file = prepare_test(
        tmp_path,
        mocker,
        initial_entries={
            entry_info.id: DumbEntry(info=entry_info, hash="sha256-old/hash")
            for entry_info in [
                DumbEntryInfo(name="one"),
                DumbEntryInfo(name="two", extra="extra"),
                DumbEntryInfo(name="three", extra="nice"),
                DumbEntryInfo(name="four"),
                DumbEntryInfo(name="five", extra="aaa"),
            ]
        },
        autocommit=autocommit,
    )

    # 2. add multiple plugins
    await Nupd(
        ImplClasses(
            mini_entry=DumbMiniEntry,
            base=DumbBaseAutocommit,
            entry=DumbEntry,
            entry_info=DumbEntryInfo,
        ),
    ).update_cmd(["one", "two@extra", "three"], autocommit=autocommit)

    # 3. check the files content
    assert (
        input_file.read_text()
        == "name,extra\none,\ntwo,extra\nthree,nice\nfour,\nfive,aaa\n"
    )
    assert json.loads(output_file.read_text()) == {
        "five": {
            "hash": "sha256-old/hash",
            "info": {"extra": "aaa", "name": "five"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "four": {
            "hash": "sha256-old/hash",
            "info": {"name": "four"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "one": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "one"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "three": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "three"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "two": {
            "hash": "sha256-some/cool/hash",
            "info": {"extra": "extra", "name": "two"},
            "some_date": "1970-01-01T00:00:00Z",
        },
    }

    # 4. check commits
    if autocommit:
        assert get_commits(tmp_path) == [
            ("example.three: update", UPDATE_THREE_PATCH),
            ("example.two: update", UPDATE_TWO_PATCH),
            ("example.one: update", UPDATE_ONE_PATCH),
        ]
