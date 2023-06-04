import asyncio
import threading

from collections import deque

from log import logger, log_stack

from config import settings


class WireRequestsWatcher:

    requests: deque
    sniff_urls: set
    block_urls: set

    def watcher(self, driver, loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_watcher(driver))

    async def async_watcher(self, driver):

        while True:
            for request in driver.requests:
                if request.url in self.sniff_urls and request.response:
                    self.requests.append(request)

            # del driver.requests
            await asyncio.sleep(1)

    def run_watcher_thread(self, driver):
        watcher_loop = asyncio.new_event_loop()
        watcher_thread = threading.Thread(
            target=self.watcher, args=(driver, watcher_loop, ), kwargs={},
        )
        watcher_thread.start()
