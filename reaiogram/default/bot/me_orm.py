
from .default import DefaultBot


class OrmMeBot(
    DefaultBot
):

    dp: None
    _me_orm: None

    async def me_orm(self):
        try:
            if self._me_orm:
                return self._me_orm
        except AttributeError:
            pass

        orm = await self.dp.orm.bot_to_orm(bot=await self.me())
        self._me_orm = orm['merged_bot']

        return self._me_orm
