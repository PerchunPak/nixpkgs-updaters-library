import dataclasses
import typing as t

import pydantic
import pytest
from frozendict import deepfreeze, frozendict
from pytest_mock import MockerFixture

from nupd import utils
from nupd.exc import GitError
from nupd.executables import Executable


def test_frozendict_type_alias() -> None:
    x = deepfreeze(frozendict({0: 0, 0.10: None, 100: [1, 2, 3]}))

    class Example(pydantic.BaseModel):
        mapping: utils.FrozenDict[int | float, float | None | tuple[int, ...]]

    obj = Example(mapping=x)
    assert isinstance(obj.mapping, frozendict)
    assert obj.mapping == x
    assert obj.model_dump() == {"mapping": x}
    json = obj.model_dump_json()
    loaded = Example.model_validate_json(json)
    assert isinstance(loaded.mapping, frozendict)
    assert loaded.mapping == x


@dataclasses.dataclass
class Dataclass:
    a: int
    b: int


@dataclasses.dataclass(frozen=True)
class DataclassFrozen:
    a: int
    b: int


class Pydantic(pydantic.BaseModel):
    a: int
    b: int


class PydanticFrozen(pydantic.BaseModel, frozen=True):
    a: int
    b: int


@pytest.mark.parametrize("cls", [Dataclass, DataclassFrozen])
def test_replace_dataclass(cls: type[Dataclass]) -> None:
    obj = cls(123, 321)
    new = utils.replace(obj, b=111)
    assert obj == cls(123, 321)
    assert new == cls(123, 111)
    assert obj is not new


@pytest.mark.parametrize("cls", [PydanticFrozen, Pydantic])
def test_replace_pydantic(cls: type[Dataclass]) -> None:
    obj = cls(a=123, b=321)
    new = utils.replace(obj, b=111)
    assert obj == cls(a=123, b=321)
    assert new == cls(a=123, b=111)
    assert obj is not new


def test_replace_something_else() -> None:
    with pytest.raises(TypeError, match="dataclass or pydantic instances"):
        _ = utils.replace(object(), a=123)


@pytest.mark.parametrize("cls", [Dataclass, DataclassFrozen])
def test_replace_unknown_field(cls: type[Dataclass]) -> None:
    obj = cls(a=123, b=321)

    with pytest.raises(TypeError, match="has no field named 'foo'"):
        _ = utils.replace(obj, foo=123)


@pytest.mark.parametrize(
    ("inp", "out"),
    [
        ("", ""),
        ("   ", ""),
        ("...", ""),
        ("a lower sentence", "Lower sentence"),
        ("The plugin is...", "Plugin is"),
        ("A the pLUGIn", "PLUGIn"),
    ],
)
def test_cleanup_raw_string(inp: str, out: str) -> None:
    assert utils.cleanup_raw_string(inp) == out


@pytest.mark.parametrize("with_revision", [False, True])
def test_cache_validate_by_revision(with_revision: bool) -> None:
    args: dict[str, t.Any] = {"input_args": {}, "time": 1}
    if with_revision:
        args["input_args"]["revision"] = "foo"

    assert utils.cache_validate_by_revision(args) is with_revision


async def test_git_commit_fails_returncode(mocker: MockerFixture) -> None:
    _ = mocker.patch.object(Executable, "GIT")
    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.returncode = 1
    mock.return_value.communicate.return_value = (
        b"stdout",
        b"stderr",
    )

    with pytest.raises(GitError, match="git returned exit code"):
        await utils.git_commit("foo")


async def test_git_commit_fails_stderr(mocker: MockerFixture) -> None:
    _ = mocker.patch.object(Executable, "GIT")
    mock = mocker.patch("asyncio.create_subprocess_exec")
    mock.return_value.returncode = 0
    mock.return_value.communicate.return_value = (
        b"stdout",
        b"stderr",
    )

    with pytest.raises(GitError, match="git wrote something to stderr"):
        await utils.git_commit("foo")
