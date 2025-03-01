import dataclasses
from pathlib import Path

import platformdirs
from nbdb.storage import SERIALIZABLE_TYPE, Storage


def get_cache_dir() -> Path:
    location = Path(platformdirs.user_cache_dir("nupd", "PerchunPak"))
    location.mkdir(parents=True, exist_ok=True)
    return location


class CacheInstance:
    def __init__(self, name: str) -> None:
        self._file: Path = get_cache_dir() / (name + ".json")
        self._storage: Storage | None = None

    async def set(self, key: str, value: SERIALIZABLE_TYPE) -> None:
        if self._storage is None:  # pragma: no cover
            self._storage = await Storage.init(self._file)

        await self._storage.set(key, value)

    async def get(self, key: str) -> SERIALIZABLE_TYPE:
        if self._storage is None:  # pragma: no cover
            self._storage = await Storage.init(self._file)

        return await self._storage.get(key)


@dataclasses.dataclass
class Cache:
    _instances: dict[str, CacheInstance] = dataclasses.field(
        default_factory=dict
    )

    def __getitem__(self, name: str) -> CacheInstance:
        if inst := self._instances.get(name):
            return inst
        inst = CacheInstance(name)
        self._instances[name] = inst
        return inst
