import asyncio
import threading

from .default import ExtraDispatcher

class TempDispatcher(ExtraDispatcher):

    new_loop: asyncio.AbstractEventLoop
    m_loop: asyncio.AbstractEventLoop

    async def _aextra_temp(self):

        # self.m_loop = asyncio.get_running_loop()
        #
        # new_loop = asyncio.new_event_loop()
        # self.new_loop = new_loop
        #
        # thread = threading.Thread(target=new_loop.run_forever)
        #
        # thread.start()

        return