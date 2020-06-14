import aiohttp
import asyncio

from bs4 import BeautifulSoup
from typing import Optional, Union, List

from contextlib import AbstractAsyncContextManager

class Webtoons(AbstractAsyncContextManager):
    BASE_URL: str = "https://www.webtoons.com"
    VIEWER_URL: str = f"{BASE_URL}/_/_/_/_/viewer" # Cool 'hack'

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop]=None):
        self._session = aiohttp.ClientSession(
            loop=loop,
            headers={"Referer": self.BASE_URL},
            cookies={"ageGatePass": True}
        )

    async def soupify(self, method: str, url: str, **kwargs) -> BeautifulSoup:
        async with self._session.request(method, url, **kwargs) as response:
            return BeautifulSoup(await response.text(), features="lxml")

    async def image_links(self, title: Union[int, str], episode: Union[int, str]) -> List[str]:
        soup = await self.soupify("GET", self.VIEWER_URL, params={"title_no": title, "episode_no": episode})
        return [img["data-url"] for img in soup("img", class_="_images")]

    async def download(self, url: Union[int, str], episode: int, index: int) -> None:
        loop = asyncio.get_event_loop()
        with open(f"{episode}_{index}.jpg", mode="wb") as f:
            async with self._session.get(url) as response:
                await loop.run_in_executor(None, f.write, await response.read())

    async def close(self) -> None:
        await self._session.close()

    async def __aexit__(self, *_) -> None:
        await self._session.close()


async def main():
    title = input("Enter title id: (95 tower of god): ")
    count = int(input("Episode count: "))
    
    async with Webtoons() as webtoons:
        for episode in range(count):
            tasks = [webtoons.download(link, episode, index) for index, link in enumerate(await webtoons.image_links(title=title, episode=episode))]
            await asyncio.gather(*tasks)
    print("Downloaded")

if __name__ == "__main__":
    asyncio.run(main())
