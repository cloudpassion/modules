import asyncio

from datetime import datetime

from log import logger


class AbstractMergedTelegram:

    id: int
    db_keys: tuple
    skip_orm: bool

    async def _default_merge_telegram(
            self, test='',
    ):

        # if merged:
        #     cl = getattr(self)
        #
        # else:
        cl = getattr(self, 'unmerged')
        if not cl:
            logger.info(f'check no {type(cl)=}, {cl=}, {self=}')
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

            if value is None:
                setattr(self, key, None)
                continue

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

    async def _deep_to_orm(
            self, test='',
            skip_to_db=False,
            only_set=False,
    ):

        # logger.info(f'{test=}, {hex(id(self))=}')
        for key in self.db_keys:

            # when early used deep_to_orm and later need to change some
            # values, need to be careful about _to_db_{key} variable

            if skip_to_db:

                cont = False
                if isinstance(skip_to_db, (list, tuple, set)):
                    for skip_key in skip_to_db:
                        if key == skip_key and hasattr(self, f'_to_db_{key}'):
                            cont = True
                            break
                else:
                    if hasattr(self, f'_to_db_{key}'):
                        cont = True

                if cont:
                    # logger.info(f'continue: {key=} in {self=}')
                    # for _tkey in self.db_keys:
                    #     try:
                    #         _db_val = getattr(self, f'_to_db_{_tkey}')
                    #     except AttributeError:
                    #         continue
                    #
                    #     logger.info(f'ch: {_tkey}: {_db_val}')
                    continue

            # if skip_to_db and hasattr(self, f'_to_db_{key}'):
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

            if isinstance(
                self_val, (
                        bytes,
                    )
            ):
                print(f'bytes:{self_val=}')

            # at end, because 0 integer 'is not' too
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
            await self_val._deep_to_orm(
                f'from_{test}', skip_to_db=skip_to_db, only_set=only_set
            )
            # await self_val._deep_to_orm(f'from_{test}')

            # logger.info(f'{self_val.to_orm=}')
            if not only_set:
                orm_val = await self_val.to_orm()
            # logger.info(f'{key=}, {orm_val=}, {self=}')

                while not orm_val:
                    # logger.info(f'wait {key=}, {self_val=}, {orm_val=}, {self=}')
                    orm_val = await self_val.from_orm()

                    await asyncio.sleep(0)

                setattr(self, f'_to_db_{key}', orm_val)

    async def _convert_to_orm(
            self,
            test='convert',
            skip_to_db=False,
            only_set=False,
    ):

        await self._deep_to_orm(test, skip_to_db=skip_to_db, only_set=only_set)
        if not only_set:
            return await self.to_orm()