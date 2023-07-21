import pytest

from log import logger

from kn.tgx.hotpicks import TGxHotPicks


@pytest.mark.asyncio
async def test_hotpicks():

    hp = TGxHotPicks()

    items = await hp.tgx_get_hot_picks(1)

    logger.info(f'{len(items)}')

