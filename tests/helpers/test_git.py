import asyncio

import pytest
from packaging.version import Version
from pytest_mock import MockerFixture

from nupd.executables import Executable
from nupd.helpers.git import (
    GitTag,
    ListGitTagsError,
    find_latest_tag,
    list_git_tags,
)

EXAMPLE_RESPONSE = b"""\
1234434314432431431243132431232432132433\tinvalid
25158ac9096ae2a64aa6ca966db272080019793c\trefs/tags/v1.0.2
1ce59cba2ae1978b875b4523ac5bead9546fdb8b\trefs/tags/v1.0.0
a213bc47ede2d4fbee20501f7af8d078bc809c9f\trefs/tags/v2.1.0
99d17d2555d13e5b7cfeaa1060c8681a855071f6\trefs/tags/v1.0.1
1849f9371e54cf511cdd8451f2b24452751edd50\trefs/tags/v2.0.0
3536745bd331210b1f345777886d7479c921558b\trefs/tags/v1.1.0
65c76402afd30427c5283127a8b6d822be8ae35f\trefs/tags/v3.1.1
6fdd62b43bf33857c0c1d63eb6d72ffed56fdb24\trefs/tags/v3.0.0
da5c415babd575516f2687fed91cbab5c2afba60\trefs/tags/v1.2.0
df54798aecd93b31dc3ce039fe75371184156deb\trefs/tags/v3.1.0
a34dd5d054d8199b81f6dddb5bb0181e837b006f\trefs/tags/v2.1.1
1234434314432431431243132431232432132433\trefs/tags/foo
1234434314432431431243132431232432132433\trefs/tags/pre-1.2.3
1234434314432431431243132431232432132433\trefs/tags/foo-123
"""
EXAMPLE_RESPONSE_OBJ = [
    GitTag(revision="25158ac9096ae2a64aa6ca966db272080019793c", reference="v1.0.2"),  # noqa: E501 # line too long
    GitTag(revision="1ce59cba2ae1978b875b4523ac5bead9546fdb8b", reference="v1.0.0"),  # noqa: E501 # line too long
    GitTag(revision="a213bc47ede2d4fbee20501f7af8d078bc809c9f", reference="v2.1.0"),  # noqa: E501 # line too long
    GitTag(revision="99d17d2555d13e5b7cfeaa1060c8681a855071f6", reference="v1.0.1"),  # noqa: E501 # line too long
    GitTag(revision="1849f9371e54cf511cdd8451f2b24452751edd50", reference="v2.0.0"),  # noqa: E501 # line too long
    GitTag(revision="3536745bd331210b1f345777886d7479c921558b", reference="v1.1.0"),  # noqa: E501 # line too long
    GitTag(revision="65c76402afd30427c5283127a8b6d822be8ae35f", reference="v3.1.1"),  # noqa: E501 # line too long
    GitTag(revision="6fdd62b43bf33857c0c1d63eb6d72ffed56fdb24", reference="v3.0.0"),  # noqa: E501 # line too long
    GitTag(revision="da5c415babd575516f2687fed91cbab5c2afba60", reference="v1.2.0"),  # noqa: E501 # line too long
    GitTag(revision="df54798aecd93b31dc3ce039fe75371184156deb", reference="v3.1.0"),  # noqa: E501 # line too long
    GitTag(revision="a34dd5d054d8199b81f6dddb5bb0181e837b006f", reference="v2.1.1"),  # noqa: E501 # line too long
    GitTag(revision="1234434314432431431243132431232432132433", reference="foo"), # noqa: E501 # line too long
    GitTag(revision="1234434314432431431243132431232432132433", reference="pre-1.2.3"), # noqa: E501 # line too long
    GitTag(revision="1234434314432431431243132431232432132433", reference="foo-123"), # noqa: E501 # line too long
]  # fmt: skip


class TestGitTag:
    def test_parsed(self) -> None:
        assert GitTag(revision="", reference="  1.2.3 ").parsed == Version(
            "1.2.3"
        )

    def test_parsed_pre_release(self) -> None:
        assert GitTag(revision="", reference="  PRE-1.2.3").parsed is None

    def test_parsed_invalid(self) -> None:
        assert GitTag(revision="", reference="foo").parsed is None


class TestListGitTags:
    @pytest.mark.parametrize("additional_arguments", [["--foo"], []])
    async def test_success(
        self, mocker: MockerFixture, additional_arguments: list[str]
    ) -> None:
        mock = mocker.patch(
            "asyncio.create_subprocess_exec",
        )
        mock.return_value.communicate.return_value = (EXAMPLE_RESPONSE, b"")
        mock.return_value.returncode = 0

        assert (
            await list_git_tags.func(
                "https://github.com/PerchunPak/nixpkgs-updaters-library",
                additional_arguments=additional_arguments
                if len(additional_arguments) > 0
                else None,
            )
            == EXAMPLE_RESPONSE_OBJ
        )

        args = [
            Executable.GIT,
            "ls-remote",
            "--tags",
            "--refs",
            "https://github.com/PerchunPak/nixpkgs-updaters-library",
        ]
        if len(additional_arguments) > 0:
            args.extend(additional_arguments)

        mock.assert_called_once_with(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    @pytest.mark.parametrize("additional_arguments", [None, ["a", "b", "c"]])
    @pytest.mark.parametrize("return_code", [0, 1])
    async def test_error(
        self,
        mocker: MockerFixture,
        additional_arguments: list[str] | None,
        return_code: int,
    ) -> None:
        mock = mocker.patch("asyncio.create_subprocess_exec")
        mock.return_value.communicate.return_value = (b"stdout", b"stderr")
        mock.return_value.returncode = return_code

        error_msg = (
            "^git ls-remote returned exit code 1\n"
            if return_code == 1
            else "^git ls-remote wrote something to stderr:\n"
        ) + "stdout=b'stdout'\nstderr=b'stderr'$"

        with pytest.raises(
            ListGitTagsError,
            match=error_msg,
        ):
            _ = await list_git_tags.func(
                "https://github.com/PerchunPak/nixpkgs-updaters-library",
                additional_arguments=additional_arguments,
            )

        args = [
            Executable.GIT,
            "ls-remote",
            "--tags",
            "--refs",
            "https://github.com/PerchunPak/nixpkgs-updaters-library",
        ]
        if additional_arguments:
            args.extend(additional_arguments)

        mock.assert_called_once_with(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )


class TestFindLatestTag:
    def test_success(self) -> None:
        assert find_latest_tag(EXAMPLE_RESPONSE_OBJ) == GitTag(
            revision="65c76402afd30427c5283127a8b6d822be8ae35f",
            reference="v3.1.1",
        )

    def test_only_invalid_tags(self) -> None:
        assert (
            find_latest_tag(
                [
                    GitTag(revision="", reference="foo"),
                    GitTag(revision="", reference="bar"),
                    GitTag(revision="", reference="baz"),
                ]
            )
            is None
        )
