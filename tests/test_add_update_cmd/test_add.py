# ruff: noqa: E101 # mixed indentation with tabs and spaces
import dataclasses
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


@dataclasses.dataclass()
class Commit:
    rev: str
    msg: str


FOUR_PATCH = """\
diff --git a/input.csv b/input.csv
--- a/input.csv
+++ b/input.csv
 name,extra\r
+four,\r
 one,\r
-two,\r
 three,\r
+two,\r
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 {
+	"four": {
+		"hash": "sha256-some/cool/hash",
+		"info": {
+			"name": "four"
+		},
+		"some_date": "1970-01-01T00:00:00Z"
+	},
 	"one": {
 		"hash": "sha256-some/cool/hash",
 		"info": {
"""
FIVE_PATCH = """\
diff --git a/input.csv b/input.csv
--- a/input.csv
+++ b/input.csv
 name,extra\r
+five,\r
 four,\r
 one,\r
 three,\r
diff --git a/output.json b/output.json
--- a/output.json
+++ b/output.json
 {
+	"five": {
+		"hash": "sha256-some/cool/hash",
+		"info": {
+			"name": "five"
+		},
+		"some_date": "1970-01-01T00:00:00Z"
+	},
 	"four": {
 		"hash": "sha256-some/cool/hash",
 		"info": {
"""


@pytest.mark.parametrize("autocommit", [False, True])
async def test_add_cmd(
    tmp_path: Path, mocker: MockerFixture, autocommit: bool
) -> None:
    input_file, output_file = prepare_test(
        tmp_path,
        mocker,
        {
            "one": DumbEntry(
                info=DumbEntryInfo(name="one"), hash="sha256-some/cool/hash"
            ),
            "two": DumbEntry(
                info=DumbEntryInfo(name="two"), hash="sha256-some/cool/hash"
            ),
            "three": DumbEntry(
                info=DumbEntryInfo(name="three"),
                hash="sha256-some/cool/hash",
            ),
        },
        autocommit,
    )

    await Nupd(
        ImplClasses(
            mini_entry=DumbMiniEntry,
            base=DumbBaseAutocommit,
            entry=DumbEntry,
            entry_info=DumbEntryInfo,
        ),
    ).add_cmd(["four", "four", "five"], autocommit=autocommit)

    assert (
        input_file.read_text()
        == "name,extra\nfive,\nfour,\none,\nthree,\ntwo,\n"
    )
    assert json.loads(output_file.read_text()) == {
        "five": {
            "hash": "sha256-some/cool/hash",
            "info": {"name": "five"},
            "some_date": "1970-01-01T00:00:00Z",
        },
        "four": {
            "hash": "sha256-some/cool/hash",
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
            "info": {"name": "two"},
            "some_date": "1970-01-01T00:00:00Z",
        },
    }

    if autocommit:
        assert get_commits(tmp_path) == [
            ("example.five: init", FIVE_PATCH),
            ("example.four: init", FOUR_PATCH),
        ]
