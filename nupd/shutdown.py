import aiohttp
import inject


class Shutdowner:
    async def shutdown(self) -> None:
        await inject.instance(aiohttp.ClientSession).close()
