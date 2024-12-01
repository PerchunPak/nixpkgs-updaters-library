import collections.abc as c
import typing as t
from contextlib import nullcontext
from inspect import (
    Parameter,
    Signature,
    _ParameterKind,  # pyright: ignore[reportPrivateUsage]
)

import pytest

from nupd.cache import (
    _get_key_for_caching,  # pyright: ignore[reportPrivateUsage]
    _recursive_to_list,  # pyright: ignore[reportPrivateUsage]
    cache_result,
    get_cache_dir,
)


@pytest.mark.parametrize(
    ("inp", "out"),
    [
        ([1, 2, 3], [1, 2, 3]),
        (
            [(1, 2), (3, 4)],
            [[1, 2], [3, 4]],
        ),
        (
            [(1, (2, 3, (4, 5, (6, 7, ("example",)))))],
            [[1, [2, 3, [4, 5, [6, 7, ["example"]]]]]],
        ),
        (
            [(("a", "b"), {"a": "b", "c": "d"}.items())],
            [[["a", "b"], [["a", "b"], ["c", "d"]]]],
        ),
    ],
)
def test_recursive_to_list(inp: c.Sequence[t.Any], out: list[t.Any]) -> None:
    assert _recursive_to_list(inp) == out


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [
        ((1, 2), {}),
        ((1,), {"b": 2}),
        ((), {"a": 1, "b": 2}),
    ],
)
@pytest.mark.parametrize(
    ("a_kind", "b_kind"),
    [
        (Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_OR_KEYWORD),
        (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY),
        (Parameter.POSITIONAL_OR_KEYWORD, Parameter.VAR_KEYWORD),
        (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_ONLY),
        (Parameter.POSITIONAL_ONLY, Parameter.KEYWORD_ONLY),
        (Parameter.POSITIONAL_ONLY, Parameter.VAR_KEYWORD),
        (Parameter.KEYWORD_ONLY, Parameter.KEYWORD_ONLY),
        (Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD),
    ],
)
def test_get_key_for_caching_simple(
    args: tuple[int],
    kwargs: dict[str, int],
    a_kind: _ParameterKind,
    b_kind: _ParameterKind,
) -> None:
    signature = Signature(
        parameters=[
            Parameter("a", a_kind),
            Parameter("b", b_kind),
        ]
    )

    if (
        # conflicting cases, expect error
        (str(signature) == "(*, a, b)" and args in ((1,), (1, 2)))
        or (str(signature) == "(a, /, *, b)" and args == (1, 2))
        or (str(signature) == "(a, *, b)" and args == (1, 2))
        or (str(signature) == "(*, a, **b)" and args in ((1,), (1, 2)))
        or (str(signature) == "(a, /, **b)" and args == (1, 2))
        or (str(signature) == "(a, **b)" and args == (1, 2))
    ):
        expectation = pytest.raises(
            RuntimeError, match="wrong amount of positional arguments"
        )
    else:
        expectation = nullcontext()

    with expectation:
        assert _get_key_for_caching(
            signature, args, kwargs, function_name="test"
        ) == {"a": 1, "b": 2}


def test_get_key_for_caching_multiple_values() -> None:
    with pytest.raises(
        TypeError, match=r"^test\(\) got multiple values for argument 'arg'$"
    ):
        _ = _get_key_for_caching(
            Signature(
                parameters=[Parameter("arg", Parameter.POSITIONAL_OR_KEYWORD)]
            ),
            args=(1,),
            kwargs={"arg": 2},
            function_name="test",
        )


def test_get_key_for_caching_var_positional() -> None:
    assert _get_key_for_caching(
        Signature(parameters=[Parameter("arg", Parameter.VAR_POSITIONAL)]),
        args=(1, 2, 3),
        kwargs={},
        function_name="test",
    ) == {"arg": [1, 2, 3]}


def test_get_key_for_caching_var_positional_1() -> None:
    assert _get_key_for_caching(
        Signature(
            parameters=[
                Parameter("a", Parameter.POSITIONAL_ONLY),
                Parameter("arg", Parameter.VAR_POSITIONAL),
            ]
        ),
        args=(1, 2, 3),
        kwargs={},
        function_name="test",
    ) == {"a": 1, "arg": [2, 3]}


@cache_result
def cached_implicitly_in_memory(n: int) -> int:
    return n * cached_implicitly_in_memory(n - 1) if n else 1


@cache_result(save_on_disk=False)
def cached_explicitly_in_memory(n: int) -> int:
    return n * cached_explicitly_in_memory(n - 1) if n else 1


@pytest.fixture
def cached_on_disk() -> c.Callable[[int], int]:
    @cache_result(save_on_disk=True, id="factorial")
    def func(n: int) -> int:
        return n * func(n - 1) if n else 1

    return func


def test_implicitly_in_memory() -> None:
    assert cached_implicitly_in_memory(10) == 3628800
    assert cached_implicitly_in_memory(5) == 120
    assert (
        str(cached_implicitly_in_memory.cache_info())  # pyright: ignore[reportFunctionMemberAccess]
        # the class is private, so we shouldn't access it
        == "CacheInfo(hits=1, misses=11, maxsize=None, currsize=11)"
    )


def test_explicitly_in_memory() -> None:
    assert cached_explicitly_in_memory(10) == 3628800
    assert cached_explicitly_in_memory(5) == 120
    assert (
        str(cached_explicitly_in_memory.cache_info())  # pyright: ignore[reportFunctionMemberAccess]
        # the class is private, so we shouldn't access it
        == "CacheInfo(hits=1, misses=11, maxsize=None, currsize=11)"
    )


def test_on_disk(cached_on_disk: c.Callable[[int], int]) -> None:
    assert cached_on_disk(10) == 3628800
    assert cached_on_disk(5) == 120
    assert (get_cache_dir() / "factorial.shelve").exists()
    assert dict(cached_on_disk._data) == {  # pyright: ignore[reportFunctionMemberAccess]
        '{"n": 0}': 1,
        '{"n": 1}': 1,
        '{"n": 2}': 2,
        '{"n": 3}': 6,
        '{"n": 4}': 24,
        '{"n": 5}': 120,
        '{"n": 6}': 720,
        '{"n": 7}': 5040,
        '{"n": 8}': 40320,
        '{"n": 9}': 362880,
        '{"n": 10}': 3628800,
    }
