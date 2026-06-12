import dataclasses
import json
import subprocess
from pathlib import Path

import pydantic_core
from pytest_mock import MockerFixture

from nupd.executables import Executable
from tests.conftest import setup_git
from tests.test_nupd_base import DumbBaseAutocommit, DumbEntry


@dataclasses.dataclass()
class Commit:
    rev: str
    msg: str


def prepare_test(
    cwd: Path,
    mocker: MockerFixture,
    initial_entries: dict[str, DumbEntry],
    autocommit: bool,
) -> tuple[Path, Path]:
    input_file = cwd / "input.csv"
    output_file = cwd / "output.json"
    _ = mocker.patch.object(DumbBaseAutocommit, "input_file", input_file)
    _ = mocker.patch.object(DumbBaseAutocommit, "output_file", output_file)

    with input_file.open("w") as f:
        _ = f.write("name,extra\r\n")
        for entry in initial_entries.values():
            _ = f.write(f"{entry.info.id},{entry.info.extra or ''}\r\n")

    _ = output_file.write_text(
        json.dumps(
            pydantic_core.to_jsonable_python(
                initial_entries, exclude_none=True
            ),
            indent="\t",
            sort_keys=True,
        )
        + "\n"
    )

    if autocommit:
        _ = subprocess.run([Executable.GIT, "init"], check=True, cwd=cwd)
        setup_git(cwd)
        _ = subprocess.run([Executable.GIT, "add", "-A"], check=True, cwd=cwd)
        _ = subprocess.run(
            [Executable.GIT, "commit", "-m", "init"], check=True, cwd=cwd
        )

    return input_file, output_file


def get_commits(cwd: Path) -> list[tuple[str, str]]:
    commits = [
        Commit(*line.strip().split(" ", 1))
        for line in subprocess.check_output(
            [Executable.GIT, "log", "--format=%H %s"],
            cwd=cwd,
        )
        .decode()
        .splitlines()
    ]
    assert commits.pop().msg == "init"
    return [
        (commit.msg, _get_commit_diff(commit.rev, cwd)) for commit in commits
    ]


def _get_commit_diff(commit: str, cwd: Path) -> str:
    return "\n".join(
        line
        for line in subprocess.check_output(
            [Executable.GIT, "diff", commit + "^!"], cwd=cwd
        )
        .decode()
        .split("\n")
        if not line.startswith("index ") and not line.startswith("@@")
    )
