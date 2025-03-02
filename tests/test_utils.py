import dataclasses
import typing as t

import pydantic
import pytest
from frozendict import deepfreeze, frozendict

from nupd import utils
from nupd.utils import chunks


@pytest.mark.parametrize(
    ("n", "result"),
    [
        (1, [[1], [2], [3], [4], [5]]),
        (3, [[1, 2, 3], [4, 5]]),
        (5, [[1, 2, 3, 4, 5]]),
    ],
)
def test_utils_chunks(n: int, result: list[list[int]]) -> None:
    assert list(chunks([1, 2, 3, 4, 5], n)) == result


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


@pytest.mark.parametrize("arg", ["abc", object()])
def test_nullify_positive(arg: t.Any) -> None:
    assert utils.nullify(arg) is arg


@pytest.mark.parametrize("arg", ["", False, None])
def test_nullify_negative(arg: t.Any) -> None:
    assert utils.nullify(arg) is None


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
