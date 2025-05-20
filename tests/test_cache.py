import typing as t

from nupd.cache import Cache, CacheInstance


async def factorial(cache: CacheInstance, n: int) -> int:
    try:
        return t.cast("int", await cache.get(str(n)))
    except KeyError:
        result = n * await factorial(cache, n - 1) if n else 1
        await cache.set(str(n), result)
        return result


async def test_cache() -> None:
    cache = Cache()["factorial"]
    assert await factorial(cache, 10) == 3628800

    storage = cache._storage  # pyright: ignore[reportPrivateUsage]
    assert storage is not None
    assert storage._data == {  # pyright: ignore[reportPrivateUsage]
        "0": 1,
        "1": 1,
        "2": 2,
        "3": 6,
        "4": 24,
        "5": 120,
        "6": 720,
        "7": 5040,
        "8": 40320,
        "9": 362880,
        "10": 3628800,
    }


def test_cache_doesnt_recreate_instance() -> None:
    cache = Cache()
    assert cache["abcde"] is cache["abcde"]
