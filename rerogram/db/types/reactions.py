import hashlib
import pyrogram

from pyrogram.raw.functions.messages import (
    GetAvailableReactions, GetMessagesReactions,
    GetMessageReactionsList,
)
from pyrogram.types import Message, List
from ...django_telegram.django_telegram.datamanager.models import (
    Message as DjangoMessage,
)

from asgiref.sync import sync_to_async, async_to_sync
from ...django_telegram.django_telegram.datamanager.models import (
    Reaction
)

from log import logger, log_stack
from ...client import MyAbstractTelegramClient


class MyTelegramReactions(
    MyAbstractTelegramClient,
):

    reaction_hash: int = 0
    available_reactions = None

    hash_strings = {
        'reaction': [
            'reaction', 'title',
        ],
    }

    def calc_hash(self, tp, strings, extra=()):
        _strings = []
        for _string in (*self.hash_strings[tp], *extra):
            try:
                string = str(strings[_string])
            except KeyError:
                continue

            _strings.append(string)

        # logger.info(f'{_strings=}')
        hash_object = hashlib.sha512(''.join(_strings).encode('utf8'))
        return hash_object.hexdigest()

    async def update_reactions(self):
        self.available_reactions = await self.invoke(
                GetAvailableReactions(hash=self.reaction_hash)
            )
        self.reaction_hash = self.available_reactions.hash

        for reaction in self.available_reactions.reactions:
            logger.info(f'{reaction}\n\n')

            r_hash = self.calc_hash(
                'reaction', {
                    'reaction': reaction.reaction,
                    'title': reaction.title,
                }
            )
            new = Reaction.objects.filter(reaction=reaction.reaction).first()
            if not new:
                force_update = False
                new = Reaction(
                    reaction=reaction.reaction,
                    title=reaction.title,
                    hash=r_hash,
                )
            else:
                force_update = True
                setattr(new, 'reaction', reaction.reaction)
                setattr(new, 'title', reaction.title)
                setattr(new, 'hash', r_hash)

            new.save(force_update=force_update)

    async def parse_reactions(
            self, message: Message, raw_data=None
    ):

        if not raw_data and hasattr(message, 'reactions') and not message.reactions:
            return

        reactions_dict = {}
        if not raw_data:
            #TODO: fix reactions
            return
            reactions = message.reactions
            for react in reactions:
                try:
                    f = await sync_to_async(Reaction.objects.filter(
                            reaction=react.emoji
                        ).first)()
                    if not f:
                        await self.update_reactions()
                    reactions_dict[
                        f.title
                    ] = {
                        'emoji': react.emoji,
                        'count': react.count,
                        # 'user_ids': [x.id for x in reactors_list] if reactors_list else []
                    }
                except:
                    log_stack.error(f'fchreact')
                    pass

        else:
            return
            new = self.db.select(
                'message',
                chat_id=chat.id, message_id=message.id
            )
            if not new:
                return

            reactions_dict = new.reactions

        # reactors_list = GetMessageReactionsList(
        #     peer=chat, id=message.id, limit=2147483646,
        #     reaction=react.emoji,
        # )
        # logger.info(f'{reactors_list=}')
        # n = 0
        # for react_line in reactors_list:
        #     peer = react_line.peer
        #     logger.info(f'{peer=}')
        #     n += 1
        #     if n > 10:
        #         break
        #
        #     if isinstance(peer, pyrogram.types.Chat):
        #         await self.chat_database(
        #             chat=peer, client=client, message=message
        #         )
        #     elif isinstance(peer, pyrogram.types.User):
        #         await self.user_database(
        #             user=peer, client=client, message=message
        #         )

        return reactions_dict
