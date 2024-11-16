import abc


class NupdBase(abc.ABC):
    def __init__(self) -> None:
        ...

    async def start(self) -> None:
        ...
