"""Tests for ``.github/commit_and_push.py``."""
import argparse
import base64
import json
import pathlib
import re
import sys
import typing
import unittest.mock

import faker as faker_package
import pytest
import pytest_mock

try:
    import git

    sys.path.append(".github")
    import commit_and_push
except ModuleNotFoundError:
    pytestmark = pytest.mark.skip("You didn't install `github_hooks` group, this test depends on this group.")

    git = unittest.mock.MagicMock()
    commit_and_push = unittest.mock.MagicMock()


@pytest.fixture(name="repo", scope="session", autouse=True)
def prepare_repo(session_mocker: pytest_mock.MockerFixture) -> unittest.mock.Mock:
    """Prepare ``repo`` variable, and return it."""
    return session_mocker.patch("commit_and_push.repo", create=True)


def test_get_repo_execute_git_add(mocker: pytest_mock.MockerFixture) -> None:
    """Tests that ``get_repo`` function calling :func:`git.Repo.git.add`."""
    mocker.patch("git.Repo")
    repo = commit_and_push._create_repo()
    repo.git.add.assert_called_once_with(".")


def test_calculate_file_content(tmp_path: pathlib.Path, faker: faker_package.Faker) -> None:
    """Tests that ``_calculate_file_content`` function returns base64 encrypted file."""
    file_content = faker.paragraph()
    with (tmp_path / "file.txt").open("w") as file:
        file.write(file_content)

    assert (
        commit_and_push._calculate_file_content(str(tmp_path / "file.txt"))
        == base64.b64encode(file_content.encode()).decode()
    )


def test_file_changes_merge(faker: faker_package.Faker) -> None:
    """Tests that ``FileChanges.merge`` function merges two :class:`.FileChanges` objects."""
    list_1, list_2, list_3, list_4 = [faker.pylist() for _ in range(4)]
    assert commit_and_push.FileChanges(additions=list_1, deletions=list_2).merge(
        commit_and_push.FileChanges(additions=list_3, deletions=list_4)
    ) == commit_and_push.FileChanges(additions=list_1 + list_3, deletions=list_2 + list_4)


def test_str_file_changes_returns_json() -> None:
    """Tests that ``str(FileChanges)`` returns JSON."""
    json.loads(str(commit_and_push.FileChanges()))


def test_str_file_changes_returns_truncated_contains_fields(faker: faker_package.Faker) -> None:
    """Tests that ``str(FileChanges)`` returns truncated :attr:`.FileAddition.contents`."""
    path = faker.word()
    assert json.loads(str(commit_and_push.FileChanges(additions=[commit_and_push.FileAddition(path, faker.word())])))[
        "additions"
    ] == [{"contents": "...", "path": path}]


@pytest.mark.parametrize("additions", (True, False))
@pytest.mark.parametrize("deletions", (True, False))
def test_bool_file_changes_return_correct_value(faker: faker_package.Faker, additions: bool, deletions: bool) -> None:
    """Tests that ``bool(FileChanges)`` returns correct value."""
    assert bool(
        commit_and_push.FileChanges(
            additions=faker.pylist() if additions else [], deletions=faker.pylist() if deletions else []
        )
    ) is (additions or deletions)


@pytest.mark.parametrize(
    "cls",
    (
        commit_and_push.NewFile("abc.txt"),
        commit_and_push.DeletedFile("abc.txt"),
        commit_and_push.RenamedFile("a.txt", "b.txt"),
    ),
)
def test_to_file_changes(
    cls: commit_and_push.NewFile, faker: faker_package.Faker, mocker: pytest_mock.MockerFixture
) -> None:
    """Tests that ``to_file_changes`` function returns :class:`.FileChanges` object."""
    mocker.patch("commit_and_push._calculate_file_content", return_value=faker.text())
    assert isinstance(cls.to_file_changes(), commit_and_push.FileChanges)


def test_get_diff_call_diff(mocker: pytest_mock.MockerFixture) -> None:
    """Tests that ``get_diff`` function calls :func:`.git.Repo.index.diff`."""
    repo = mocker.patch("commit_and_push.repo", create=True)
    commit_and_push.get_diff()
    repo.index.diff.assert_called_once_with(None, staged=True)


def test_git_pull_call_pull(mocker: pytest_mock.MockerFixture) -> None:
    """Tests that ``_git_pull`` function calls :func:`.git.Repo.remotes.origin.pull`."""
    repo = mocker.patch("commit_and_push.repo", create=True)
    commit_and_push._git_pull()
    repo.remotes.origin.pull.assert_called_once_with()


def test_generate_request_data_return_valid_data(faker: faker_package.Faker, mocker: pytest_mock.MockerFixture) -> None:
    """Tests that ``generate_request_data`` function returns valid data."""
    commit = mocker.patch("commit_and_push.get_latest_commit", return_value=faker.sha256())()
    args = argparse.Namespace(repository=faker.word(), branch=faker.word(), message=faker.text(), token=faker.text())

    assert commit_and_push.generate_request_data(args, commit_and_push.FileChanges(additions=[], deletions=[])) == (
        ("https://api.github.com/graphql",),
        {
            "headers": {
                "Authorization": f"bearer {args.token}",
                "Accept": "application/vnd.github.v4.idl",
            },
            "data": json.dumps(
                {
                    "query": "mutation ($input: CreateCommitOnBranchInput!) {createCommitOnBranch(input: $input) {commit {url}}}",
                    "variables": {
                        "input": {
                            "branch": {"repositoryNameWithOwner": args.repository, "branchName": args.branch},
                            "message": {"headline": args.message},
                            "fileChanges": {"additions": [], "deletions": []},
                            "expectedHeadOid": commit,
                        }
                    },
                }
            ),
        },
    )


def test_send_http_request_call_required_functions(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``send_http_request`` function calls required functions."""
    response = mocker.patch("requests.post")
    passed_args = faker.pytuple(), faker.pydict()
    generator = commit_and_push.send_http_request(*passed_args)
    next(generator)
    response.assert_called_once_with(*passed_args[0], **passed_args[1])
    response.return_value.json.assert_called_once_with()

    with pytest.raises(StopIteration):
        next(generator)

    response.return_value.raise_for_status.assert_called_once_with()


def test_send_http_request_run_code_only_once(mocker: pytest_mock.MockerFixture) -> None:
    """Tests that ``send_http_request`` function run code in ``for`` block only once."""
    mocker.patch("requests.post")
    for i, _ in enumerate(commit_and_push.send_http_request((), {})):
        assert i == 0


def test_send_http_request_error_handling(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``send_http_request`` function correctly handling errors."""
    response = mocker.patch("requests.post")
    response.return_value.json.return_value = {"errors": [{"message": faker.sentence()} for _ in range(faker.pyint(2, 5))]}
    generator = commit_and_push.send_http_request((), {})
    next(generator)

    with pytest.raises(ValueError, match=re.escape("Github raised error(s): \n" + "\n".join(error["message"] for error in response.return_value.json.return_value["errors"]))):
        try:
            next(generator)
        except StopIteration:
            pass


def test_get_latest_commit_returns_latest_commit(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``get_latest_commit`` function returns latest commit."""
    repo = mocker.patch("commit_and_push.repo", create=True)
    repo.rev_parse.return_value = faker.sha256()
    assert commit_and_push.get_latest_commit() == repo.rev_parse.return_value
    repo.rev_parse.asser_was_called_once_with("HEAD")


def test_get_welcome_info(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``get_welcome_info`` function returns welcome info."""
    commit = mocker.patch("commit_and_push.get_latest_commit", return_value=faker.sha256())()
    args = argparse.Namespace(repository=faker.word(), branch=faker.word(), message=faker.text(), token=faker.text())

    assert commit_and_push.get_welcome_info(args) == f"""\
Repository to commit and push: '{args.repository}'.
Branch to commit and push: '{args.branch}'.
Commit message: '{args.message}'.
Latest commit: '{commit}'\
"""


def test_calculate_file_changes_returns_none_if_diff_is_empty() -> None:
    """Tests that ``calculate_file_changes`` function returns :obj:`.None` object if diff is empty."""
    assert commit_and_push.calculate_file_changes([]) is None


@pytest.fixture
def diff_item(faker: faker_package.Faker) -> typing.Callable[[typing.Optional[str]], git.Diff]:
    """Returns factory for :class:`git.Diff` object."""

    class DiffItem:
        def __init__(self, cls: typing.Optional[str]) -> None:
            change_types = {
                "commit_and_push.NewFile": "A",
                "commit_and_push.DeletedFile": "D",
                "commit_and_push.RenamedFile": "R",
                "commit_and_push.ModifiedFile": "M",
            }
            self.change_type = faker.random_element(change_types.values()) if cls is None else change_types[cls]

            self.a_path = faker.file_path()
            self.b_path = faker.file_path()

    return typing.cast(typing.Callable[[typing.Optional[str]], git.Diff], DiffItem)


def test_calculate_file_changes_return_file_changes(
    diff_item: typing.Callable[[typing.Optional[str]], git.Diff], mocker: pytest_mock.MockerFixture
) -> None:
    """Tests that ``calculate_file_changes`` function returns :class:`.FileChanges` object."""
    mocker.patch("commit_and_push._calculate_file_content", return_value="...")
    assert isinstance(commit_and_push.calculate_file_changes([diff_item(None)]), commit_and_push.FileChanges)


@pytest.mark.parametrize(
    "cls",
    (
        "commit_and_push.NewFile",
        "commit_and_push.DeletedFile",
        "commit_and_push.RenamedFile",
        "commit_and_push.ModifiedFile",
    ),
)
def test_calculate_file_changes_modes(
    cls: str, diff_item: typing.Callable[[typing.Optional[str]], git.Diff], mocker: pytest_mock.MockerFixture
) -> None:
    """Tests that ``calculate_file_changes`` function working with all possible ``change_type``s."""
    diff = diff_item(cls)
    mocker.patch("commit_and_push._calculate_file_content", return_value="...")

    if diff.change_type == "A":
        expected = commit_and_push.NewFile(path=diff.a_path).to_file_changes()
    elif diff.change_type == "D":
        expected = commit_and_push.DeletedFile(path=diff.b_path).to_file_changes()
    elif diff.change_type == "R":
        expected = commit_and_push.RenamedFile(new_path=diff.b_path, old_path=diff.a_path).to_file_changes()
    elif diff.change_type == "M":
        expected = commit_and_push.ModifiedFile(path=diff.b_path).to_file_changes()
    else:
        raise ValueError(f"Unknown change type: {diff.change_type}")

    assert commit_and_push.calculate_file_changes([diff]) == expected


def assert_not_called(*mocked: unittest.mock.Mock) -> None:
    """Asserts that all mocked objects were not called."""
    for mocked_object in mocked:
        mocked_object.assert_not_called()


def test_main_calls_right_order(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``main`` function calls right order of required functions."""
    parse_args = mocker.patch("commit_and_push.parse_args")
    get_welcome_info = mocker.patch("commit_and_push.get_welcome_info")
    get_diff = mocker.patch("commit_and_push.get_diff")
    calculate_file_changes = mocker.patch("commit_and_push.calculate_file_changes")
    generate_request_data = mocker.patch("commit_and_push.generate_request_data", return_value=faker.pytuple())
    send_http_request, commit_url = mocker.patch("commit_and_push.send_http_request"), faker.url()
    send_http_request.return_value = ({'data': {'createCommitOnBranch': {'commit': {'url': commit_url}}}},)
    git_pull = mocker.patch("commit_and_push._git_pull")
    mocked = [parse_args, get_welcome_info, get_diff, calculate_file_changes, generate_request_data, send_http_request, git_pull]

    main_func = commit_and_push.main()
    assert_not_called(*mocked)

    next(main_func)
    parse_args.assert_called_once_with()
    mocked.pop(0)
    get_welcome_info.assert_called_once_with(parse_args.return_value)
    mocked.pop(0)
    assert_not_called(*mocked)

    next(main_func)
    get_diff.assert_called_once_with()
    mocked.pop(0)
    calculate_file_changes.assert_called_once_with(get_diff.return_value)
    mocked.pop(0)
    assert_not_called(*mocked)

    next(main_func)
    generate_request_data.assert_called_once_with(parse_args.return_value, calculate_file_changes.return_value)
    mocked.pop(0)
    send_http_request.assert_called_once_with(*generate_request_data.return_value)
    mocked.pop(0)
    assert_not_called(*mocked)

    next(main_func)
    assert_not_called(*mocked)

    next(main_func)
    git_pull.assert_called_once_with()
    mocked.pop(0)
    assert_not_called(*mocked)

    with pytest.raises(StopIteration):
        next(main_func)
    assert_not_called(*mocked)


def test_main_yields_right_order(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``main`` function yields right values."""
    mocker.patch("commit_and_push.parse_args")
    get_welcome_info = mocker.patch("commit_and_push.get_welcome_info")
    mocker.patch("commit_and_push.get_diff")
    calculate_file_changes = mocker.patch("commit_and_push.calculate_file_changes")
    mocker.patch("commit_and_push.generate_request_data", return_value=faker.pytuple())
    send_http_request, commit_url = mocker.patch("commit_and_push.send_http_request"), faker.url()
    send_http_request.return_value = ({'data': {'createCommitOnBranch': {'commit': {'url': commit_url}}}},)
    mocker.patch("commit_and_push._git_pull")

    main_func = commit_and_push.main()

    assert next(main_func) == get_welcome_info.return_value
    assert next(main_func) == "File changes: " + str(calculate_file_changes.return_value)
    assert next(main_func) == f"\nResponse from GitHub: {send_http_request.return_value[0]}"
    assert next(main_func) == "\nPerforming `git pull`..."
    assert next(main_func) == f"Congratulations! I'm done! Here is the link to your commit: {commit_url}"

    with pytest.raises(StopIteration):
        next(main_func)


def test_main_returns_on_no_changes(mocker: pytest_mock.MockerFixture, faker: faker_package.Faker) -> None:
    """Tests that ``main`` returns on no changes."""
    mocker.patch("commit_and_push.parse_args")
    mocker.patch("commit_and_push.get_welcome_info")
    mocker.patch("commit_and_push.get_diff")
    mocker.patch("commit_and_push.calculate_file_changes", return_value=())
    generate_request_data = mocker.patch("commit_and_push.generate_request_data", return_value=faker.pytuple())
    send_http_request, commit_url = mocker.patch("commit_and_push.send_http_request"), faker.url()
    send_http_request.return_value = ({'data': {'createCommitOnBranch': {'commit': {'url': commit_url}}}},)
    git_pull = mocker.patch("commit_and_push._git_pull")

    main_func = commit_and_push.main()

    next(main_func)
    next(main_func)

    with pytest.raises(StopIteration):
        assert next(main_func) == "Nothing to commit."
    assert_not_called(generate_request_data, send_http_request, git_pull)
