from datetime import datetime
from collections import deque, defaultdict
import pyrogram

from pyrogram import Client as PyrogramClient
from pyrogram.methods.utilities.idle import idle
from pyrogram.raw.functions.messages import (
    GetAvailableReactions, ReadReactions, GetMessagesReactions
)
from pyrogram.types import (
    InputMediaDocument,
    InputMediaPhoto,
    Document,
    Photo, Video, Voice, Audio,
    Sticker, Animation,
    Contact, VideoNote, Location,

)

from pyrogram import raw
from pyrogram.raw.core import TLObject
from pyrogram.session import Session

from config import settings, secrets
from atiny.file import create_dir, create_date_dir
from log import logger, log_stack, flogger

from ..listener import MyPyrogramListener
from ..functions import MyPyrogramFunctions
from ..rewrite import MyPyrogramRewrite

from ..db import SqlDatabase


class MyTelegramClient(
    MyPyrogramListener,
    MyPyrogramFunctions,
    PyrogramClient,
    MyPyrogramRewrite,
):

    def __init__(self):

        # auth
        _session_name = secrets.telegram.session_name
        _session_id = f'{datetime.now().strftime("%d.%m.%Y_%H.%M.%S")}_' \
                      f'{_session_name}'
        _api_id = secrets.telegram.api_id
        _api_hash = secrets.telegram.api_hash

        # config

        super(MyTelegramClient, self).__init__(
            name=_session_name,
            # api get from https://my.telegram.org
            api_id=_api_id,
            api_hash=_api_hash,
        )

        # misc
        self.timezone_offset = settings.misc.timezone_offset
        self.timezone_name = settings.misc.timezone_name

        # log, session
        dated_dir = create_date_dir(
            '/home/mg/trash/logs/pyrogram_session_logs'
        )
        create_dir(dated_dir)
        self.log_session_file = f'{dated_dir}/{_session_id}.txt'

        self.db = SqlDatabase

        self.on_start_functions = deque()
        self.on_start_data = {}

        self.discussion_fwd_data = {}
        self.discussion_fwd_skip = {}

        self.media_ext = defaultdict(lambda: 'txt', {

            # video
            pyrogram.types.Video: 'mp4',
            pyrogram.enums.MessageMediaType.VIDEO: 'mp4',
            # photo
            pyrogram.types.Photo: 'jpg',
            pyrogram.enums.MessageMediaType.PHOTO: 'jpg',
            # doc
            pyrogram.enums.MessageMediaType.DOCUMENT: 'txt',
            pyrogram.types.Document: 'txt',

            # pyrogram.types.Voice: self.send_voice,
            # pyrogram.enums.MessageMediaType.VOICE: self.send_voice,
            #
            # pyrogram.types.Audio: self.send_audio,
            # pyrogram.enums.MessageMediaType.AUDIO: self.send_audio,
            #
            # pyrogram.types.VideoNote: self.send_video_note,
            # pyrogram.enums.MessageMediaType.VIDEO_NOTE: self.send_video_note,

        })

        self.media_functions = defaultdict(lambda: self.send_document, {

            # video
            pyrogram.types.Video: self.send_video,
            pyrogram.enums.MessageMediaType.VIDEO: self.send_video,
            # photo
            pyrogram.types.Photo: self.send_photo,
            pyrogram.enums.MessageMediaType.PHOTO: self.send_photo,
            # doc
            pyrogram.enums.MessageMediaType.DOCUMENT: self.send_document,
            pyrogram.types.Document: self.send_document,

            pyrogram.types.Sticker: self.send_sticker,
            pyrogram.enums.MessageMediaType.STICKER: self.send_sticker,

            pyrogram.types.Animation: self.send_animation,
            pyrogram.enums.MessageMediaType.ANIMATION: self.send_animation,

            pyrogram.types.Voice: self.send_voice,
            pyrogram.enums.MessageMediaType.VOICE: self.send_voice,

            pyrogram.types.Audio: self.send_audio,
            pyrogram.enums.MessageMediaType.AUDIO: self.send_audio,

            pyrogram.types.Contact: self.send_contact,
            pyrogram.enums.MessageMediaType.CONTACT: self.send_contact,

            pyrogram.types.VideoNote: self.send_video_note,
            pyrogram.enums.MessageMediaType.VIDEO_NOTE: self.send_video_note,

            pyrogram.types.Location: self.send_location,
            pyrogram.enums.MessageMediaType.LOCATION: self.send_location,

        })

        self.media_kwargs = defaultdict(lambda: [], {

            pyrogram.types.Video: ('video', ),
            pyrogram.enums.MessageMediaType.VIDEO: ('video', ),

            pyrogram.types.Photo: ('photo', ),
            pyrogram.enums.MessageMediaType.PHOTO: ('photo', ),

            pyrogram.types.Document: ('document', 'file_name', ),
            pyrogram.enums.MessageMediaType.DOCUMENT: (
                'document', 'file_name', ),

            pyrogram.types.Sticker: ('sticker', ),
            pyrogram.enums.MessageMediaType.STICKER: ('sticker', ),

            pyrogram.types.Animation: ('animation', ),
            pyrogram.enums.MessageMediaType.ANIMATION: ('animation', ),

            pyrogram.types.Voice: ('voice', ),
            pyrogram.enums.MessageMediaType.VOICE: ('voice', ),

            pyrogram.types.Audio: ('audio', 'file_name', 'title', ),
            pyrogram.enums.MessageMediaType.AUDIO: ('audio', 'file_name', 'title', ),

            pyrogram.types.Contact: (
                'contact', 'phone_number', 'first_name', 'last_name', ),
            pyrogram.enums.MessageMediaType.CONTACT: (
                'contact', 'phone_number', 'first_name', 'last_name', ),

            pyrogram.types.VideoNote: ('video_note', ),
            pyrogram.enums.MessageMediaType.VIDEO_NOTE: ('video_note', ),

            pyrogram.types.Location: (
                'location', 'latitude', 'longitude', ),
            pyrogram.enums.MessageMediaType.LOCATION: (
                'location', 'latitude', 'longitude', ),
        })

        self.media_fwd_class = defaultdict(lambda: Document, {

            pyrogram.types.Document: Document,
            pyrogram.enums.MessageMediaType.DOCUMENT: Document,

            pyrogram.types.Video: Video,
            pyrogram.enums.MessageMediaType.VIDEO: Video,

            pyrogram.types.Photo: Photo,
            pyrogram.enums.MessageMediaType.PHOTO: Photo,

            pyrogram.types.Sticker: Sticker,
            pyrogram.enums.MessageMediaType.STICKER: Sticker,

            pyrogram.types.Animation: Animation,
            pyrogram.enums.MessageMediaType.ANIMATION: Animation,

            pyrogram.types.Voice: Voice,
            pyrogram.enums.MessageMediaType.VOICE: Voice,

            pyrogram.types.Audio: Audio,
            pyrogram.enums.MessageMediaType.AUDIO: Audio,

            pyrogram.types.Contact: Contact,
            pyrogram.enums.MessageMediaType.CONTACT: Contact,

            pyrogram.types.VideoNote: VideoNote,
            pyrogram.enums.MessageMediaType.VIDEO_NOTE: VideoNote,

            pyrogram.types.Location: Location,
            pyrogram.enums.MessageMediaType.LOCATION: Location,

        })

        self.media_type_kw = defaultdict(lambda: 'document', {

            pyrogram.types.Document: 'document',
            pyrogram.enums.MessageMediaType.DOCUMENT: 'document',

            pyrogram.types.Video: 'video',
            pyrogram.enums.MessageMediaType.VIDEO: 'video',

            pyrogram.types.Photo: 'photo',
            pyrogram.enums.MessageMediaType.PHOTO: 'photo',

            pyrogram.types.Sticker: 'sticker',
            pyrogram.enums.MessageMediaType.STICKER: 'sticker',

            pyrogram.types.Animation: 'animation',
            pyrogram.enums.MessageMediaType.ANIMATION: 'animation',

            pyrogram.types.Voice: 'voice',
            pyrogram.enums.MessageMediaType.VOICE: 'voice',

            pyrogram.types.Audio: 'audio',
            pyrogram.enums.MessageMediaType.AUDIO: 'audio',

            pyrogram.types.Contact: 'contact',
            pyrogram.enums.MessageMediaType.CONTACT: 'contact',

            pyrogram.types.VideoNote: 'video_note',
            pyrogram.enums.MessageMediaType.VIDEO_NOTE: 'video_note',

            pyrogram.types.Location: 'location',
            pyrogram.enums.MessageMediaType.LOCATION: 'location',

        })

        self.fwd_skip_group = {}
        self.media_group_messages = defaultdict(lambda: [], {})

    async def init_func(self):
        await self.load_discussion_forward()
        self.load_database_data()
        # await self.update_reactions()
        while True:
            try:
                link, func = self.on_start_functions.popleft()
            except IndexError:
                break

            logger.info(f'run on start: {func}')
            self.on_start_data[link] = await func

    async def on_start(self, link, func):
        self.on_start_functions.append((link, func))

    async def client_start(self, forever=True):
        await self.start()
        logger.info(f'start')
        await self.init_func()
        logger.info(f'init_func')
        logger.info(f'{forever=}\n')

        if forever:
            await idle()
            logger.info(f'disconnected')

        await self.stop()
        logger.info(f'stop')

    async def invoke(
            self: "pyrogram.Client",
            query: TLObject,
            retries: int = 10,
            timeout: float = 60.0,
            sleep_threshold: float = None
    ):
        """Invoke raw Telegram functions.

        This method makes it possible to manually call every single Telegram API method in a low-level manner.
        Available functions are listed in the :obj:`functions <pyrogram.api.functions>` package and may accept compound
        data types from :obj:`types <pyrogram.api.types>` as well as bare types such as ``int``, ``str``, etc...

        .. note::

            This is a utility method intended to be used **only** when working with raw
            :obj:`functions <pyrogram.api.functions>` (i.e: a Telegram API method you wish to use which is not
            available yet in the Client class as an easy-to-use method).

        Parameters:
            query (``RawFunction``):
                The API Schema function filled with proper arguments.

            retries (``int``):
                Number of retries.

            timeout (``float``):
                Timeout in seconds.

            sleep_threshold (``float``):
                Sleep threshold in seconds.

        Returns:
            ``RawType``: The raw type response generated by the query.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if not self.is_connected:
            raise ConnectionError("Client has not been started yet")

        if self.no_updates:
            query = raw.functions.InvokeWithoutUpdates(query=query)

        if self.takeout_id:
            query = raw.functions.InvokeWithTakeout(takeout_id=self.takeout_id, query=query)

        r = await self.session.invoke(
            query, retries, timeout,
            (sleep_threshold
             if sleep_threshold is not None
             else self.sleep_threshold)
        )

        await self.fetch_peers(getattr(r, "users", []))
        await self.fetch_peers(getattr(r, "chats", []))

        return r
