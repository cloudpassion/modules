import pyrogram
import re

from typing import Union

from log import log_stack


class MyPyrogramEntities:

    async def add_entites(
            self, text, bolds=[], underlines=[], italic=[], links=[],
            text_mentions=[], old_entities=[],
    ):
        entities = []
        entities_edited = False
        added_offset = set()

        if old_entities:
            for old_ent in old_entities:
                old_ent: pyrogram.types.MessageEntity
                offset = old_ent.offset
                old_len = old_ent.length

                for n in range(offset, offset+old_len+1):
                    added_offset.add(n)

        for new_ent in (
                *bolds, *underlines, *italic, *links, *text_mentions,
        ):
            num = 0
            tp = None
            extra = {}
            if isinstance(new_ent, (list, tuple)):
                tp = new_ent[0]
                if tp == 'TEXT_MENTION':
                    tp = pyrogram.enums.MessageEntityType.TEXT_MENTION
                    extra = {'user': new_ent[2]}
                    try:
                        num = new_ent[3]
                    except:
                        pass
                    new_ent = new_ent[1]
                else:
                    tp = pyrogram.enums.MessageEntityType.TEXT_LINK
                    extra = {'url': new_ent[1]}
                    new_ent = new_ent[0]
            else:
                if new_ent in bolds:
                    tp = pyrogram.enums.MessageEntityType.BOLD
                if new_ent in underlines:
                    tp = pyrogram.enums.MessageEntityType.UNDERLINE
                if new_ent in italic:
                    tp = pyrogram.enums.MessageEntityType.ITALIC

            if not tp:
                continue

            letter_index = None
            try:
                # letter_index = text.lower().index(new_ent.lower(), num)
                letter_index = [
                    m.start() for m in re.finditer(new_ent.lower(), text.lower())
                ][num]
            except IndexError:
                continue
            except:
                log_stack.error(f'l_i')
                continue

            if not letter_index:
                continue

            entity = pyrogram.types.MessageEntity(
                type=tp,
                offset=letter_index, length=len(new_ent),
                **extra,
            )
            entities.append(entity)

            for n in range(letter_index, letter_index+len(new_ent)+1):
                added_offset.add(n)

        if not old_entities:
            return entities, added_offset, entities_edited
        else:
            for old_ent in old_entities:
                if old_ent not in entities:
                    entities.append(old_ent)
                    entities_edited = True

            return entities, added_offset, entities_edited
