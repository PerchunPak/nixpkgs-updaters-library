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
