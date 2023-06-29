import asyncio

from datetime import datetime

from log import logger


class AbstractMergedTelegram:

    id: int
    db_keys: tuple

    async def _default_merge_telegram(
            self, test='',
    ):

        # if merged:
        #     cl = getattr(self)
        #
        # else:
        cl = getattr(self, 'unmerged')
        if not cl:
            # logger.info(f'check no {type(cl)=}, {cl=}')
            return

        # logger.info(f'{test=}, {hex(id(self))=}, {type(cl)=}, {self=}')

        for key in self.db_keys:

            # if hasattr(self, f'_to_db_{key}'):
            #     logger.info(f'continue2: {key=} in {hex(id(self))=}')
            #     continue

            # logger.info(f'{key=}, {type(cl)=}')
            try:
                value = getattr(cl, key)
                # logger.info(f'{value=}')
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

            # logger.info(f'{key=}, {value=}, {self=}')
            setattr(self, key, value)

        # await self._deep_to_orm(test)

    async def _deep_to_orm(self, test=''):

        # logger.info(f'{test=}, {hex(id(self))=}')
        for key in self.db_keys:

            # logger.info(f'{key=}, {self=}')
            # if hasattr(self, f'_to_db_{key}'):
            #     # logger.info(f'continue: {key=} in {self=}')
            #     continue

            # logger.info(f'{key=}, {self=}')
            try:
                self_val = getattr(self, key)
            except AttributeError:
                # logger.info(f'no {key} in {self=}')
                setattr(self, key, None)
                setattr(self, f'_to_db_{key}', None)
                continue

            # logger.info(f'{key=}, {self_val=}')

            if isinstance(
                self_val, datetime
            ):
                setattr(self, f'_to_db_{key}', int(self_val.strftime('%s')))
                continue

            if isinstance(
                    self_val, (
                            int, str, bool
                    )
            ):
                setattr(self, f'_to_db_{key}', self_val)
                continue

            # at end, because 0 inteter 'is not' too
            if not self_val:
                setattr(self, f'_to_db_{key}', None)
                continue

            # logger.info(f'{key=}, {self_val=}, {getattr(self, key)}')

            # if not hasattr(self_val, 'unmerged'):
            #     logger.info(f'check {key=}, {self_val=}, {self=}')

            # if self_val.unmerged is None:
            #     # run to orm
            #     merge_func = self_val.merge_func
            #     merge_key = self_val.merge_key
            #     merge_coro = getattr(self_val, merge_func)
            #     await self.merge_coro()

            # await self_val._default_merge_telegram(f'from_{test}')
            # while True:
            #     br = False
            #     for d_key in self_val.select_keys:
            #         try:
            #             att = getattr(self_val, d_key)
            #             logger.info(f'ok: {d_key} -> {att=}')
            #             br = True
            #             break
            #         except AttributeError:
            #             logger.info(f'{test=}, get att {d_key=} in {self_val=}')
            #             quit()
            #     if br:
            #         break

            # logger.info(f'{self_val=}, {self=}')
            # self_val._default_merge_telegram(f'from_{test}')
            await self_val._deep_to_orm(f'from_{test}')
            # await self_val._deep_to_orm(f'from_{test}')

            # logger.info(f'{self_val.to_orm=}')
            orm_val = await self_val.to_orm()
            # logger.info(f'{key=}, {orm_val=}, {self=}')

            while not orm_val:
                # logger.info(f'{key=}, {orm_val=}, {self=}')
                orm_val = await self_val.from_orm()
                await asyncio.sleep(0)

            setattr(self, f'_to_db_{key}', orm_val)

    async def _convert_to_orm(self, test='convert'):

        await self._deep_to_orm(test)
        return await self.to_orm()
