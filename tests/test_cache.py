import collections.abc as c
import typing as t

import pytest

from nupd.cache import (
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
        "[[0], []]": 1,
        "[[1], []]": 1,
        "[[2], []]": 2,
        "[[3], []]": 6,
        "[[4], []]": 24,
        "[[5], []]": 120,
        "[[6], []]": 720,
        "[[7], []]": 5040,
        "[[8], []]": 40320,
        "[[9], []]": 362880,
        "[[10], []]": 3628800,
    }
