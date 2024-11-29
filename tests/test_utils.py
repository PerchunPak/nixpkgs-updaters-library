import pytest

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
