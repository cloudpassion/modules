import asyncio

try:
    from log import logger, log_stack, parse_traceback
except ImportError:
    from ...log import logger, log_stack, parse_traceback

try:
    import aiohttp
except ImportError:
    logger.info(f'need install aiohttp for MyHttpSimulate')

try:
    import aresponses
except ImportError:
    logger.info(f'need install aresponses for response simulate')


from ..merge import MergeResp

from .default import MyHttpDefault


class MyHttpSimulate(
    MyHttpDefault,
):

    async def _get_aresponse(
            self, url='http://ggg', code=200,
            response='simulate', content_type='text/html'
    ):

        async with aresponses.ResponsesMockServer() as arsps:
            arsps.add(''.join(url.split('/')[2:]), '/', 'get',
                      arsps.Response(
                          body=response,
                          headers={"Content-Type": content_type}
                      )
                      )

            async with aiohttp.ClientSession() as session:

                async with session.get(url) as response:
                    text = await response.text()
                    _content = await response.read()

        return False, _content, MergeResp(
            text=text, headers=response.headers, status=code
        )
