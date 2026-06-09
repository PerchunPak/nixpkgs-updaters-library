import aiohttp
import inject


class Shutdowner:  # pragma: no cover
    async def shutdown(self) -> None:
        await inject.instance(aiohttp.ClientSession).close()
