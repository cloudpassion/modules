import asyncio

from datetime import datetime

from log import logger


class AbstractMergedTelegram:

    id: int
    db_keys: tuple

    async def _default_merge_telegram(
            self,
    ):

        cl = getattr(self, 'unmerged')

        for key in self.db_keys:

            # logger.info(f'{key=}, {cl=}')
            try:
                value = getattr(cl, key)
            except AttributeError:
                continue

            # if value is None:
            #     continue
            #
            if not isinstance(
                    value, (
                        int, str, bool,
                        datetime,
                    )
            ):
                # logger.info(f'skip {key}, {value=}, {type(value)=}')
                continue

            # logger.info(f'{key=}, {value=}')
            setattr(self, key, value)

    async def _deep_to_orm(self):

        for key in self.db_keys:

            # logger.info(f'{key=}, {self=}')
            try:
                self_val = getattr(self, key)
            except AttributeError:
                continue

            # logger.info(f'{key=}, {self_val=}')

            if isinstance(
                self_val, datetime
            ):
                setattr(self, f'db_{key}', int(self_val.strftime('%s')))
                continue

            if isinstance(
                    self_val, (
                            int, str, bool
                    )
            ):
                setattr(self, f'db_{key}', self_val)
                continue

            if self_val.unmerged is None:
                setattr(self, f'db_{key}', None)
                continue

            await self_val._deep_to_orm()

            orm_val = await self_val.to_orm()
            # logger.info(f'{key=}, {orm_val=}, {self=}')

            while not orm_val:
                # logger.info(f'{key=}, {orm_val=}, {self=}')
                orm_val = await self_val.from_orm()
                await asyncio.sleep(0)

            setattr(self, f'db_{key}', orm_val)

    async def _convert_to_orm(self):

        await self._deep_to_orm()
        return await self.to_orm()
