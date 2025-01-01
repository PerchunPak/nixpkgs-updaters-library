import aiohttp
import inject
from nbdb.storage import Storage


class Shutdowner:
    async def shutdown(self) -> None:
        await inject.instance(aiohttp.ClientSession).close()

        for inst in Storage.instances:
            await inst.write()
