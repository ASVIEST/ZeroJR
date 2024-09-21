import record
import async_chain

class AttachmentGen:
    _filename: str
    _url: str
    _is_spoiler: bool

    def __init__(self) -> None:
        self._filename = "default"
        self._url = "default"
        self._is_spoiler = False
    
    @async_chain.method
    async def with_filename(self, filename: str):
        self._filename = filename
        return self
    
    @async_chain.method
    async def with_url(self, url: str):
        self._url = url
        return self
    
    @async_chain.method
    async def with_is_spoiler(self, is_spoiler: bool):
        self._is_spoiler = is_spoiler
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.Attachment(
            filename = self._filename,
            url = self._url,
            is_spoiler = self._is_spoiler
        )

class MessageGen:
    _display_name : str
    _display_avatar_url : str
    _content : str
    _thread: record.Thread | None
    _attachments: list[record.Attachment]

    def __init__(self):
        self._display_name = "default"
        self._display_avatar_url = ""
        # self._content is required
        self._thread = None
        self._attachments = []
    
    @async_chain.method
    async def with_display_name(self, display_name: str):
        self._display_name = display_name
        return self
    
    @async_chain.method
    async def with_display_avatar_url(self, url: str):
        self._display_avatar_url = url
        return self
    
    @async_chain.method
    async def with_content(self, content: str):
        self._content = content
        return self

    @async_chain.method
    async def with_thread(self, gen_func):
        gen = ThreadGen()
        gen = await gen_func(gen)
        self._thread = await gen.get_result()
        return self
    
    @async_chain.method
    async def with_attachment(self, gen_func):
        gen = AttachmentGen()
        gen = await gen_func(gen)
        self._attachments.append(await gen.get_result())
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.Message(
            display_name = self._display_name,
            display_avatar_url = self._display_avatar_url,
            content = self._content,
            thread = self._thread,
            attachments = tuple(self._attachments)
        )

class HistoryGen:
    _messages: list[record.Message]

    def __init__(self):
        self._messages = []
    
    @async_chain.method
    async def with_message(self, gen_func):
        gen = MessageGen()
        gen = await gen_func(gen)
        self._messages.append(await gen.get_result())
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.History(
            messages = tuple(self._messages)
        )

class ThreadGen:
    _auto_archive_duration : int
    _invitable : bool
    _locked : bool
    _name : str
    _slowmode_delay : int
    _archived : bool
    _type : record.ThreadType
    _members_id : list[int]
    _history: record.History

    def __init__(self):
        self._auto_archive_duration = 0
        self._invitable = True
        self._locked = False
        self._name = "default"
        self._slowmode_delay = 0
        self._archived = False
        self._type = record.ThreadType.public_thread
        self._members_id = []
        self._history = record.History(messages = ())

    @async_chain.method
    async def with_auto_archive_duration(self, type: record.ThreadType):
        self._auto_archive_duration = type
        return self
    
    @async_chain.method
    async def with_invitable(self, invitable: bool):
        self._invitable = invitable
        return self
    
    @async_chain.method
    async def with_locked(self, locked: bool):
        self._locked = locked
        return self
    
    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self
    
    @async_chain.method
    async def with_slowmode_delay(self, val: int):
        self._slowmode_delay = val
        return self
    
    @async_chain.method
    async def with_archived(self, archived: int):
        self._archived = archived
        return self
    
    @async_chain.method
    async def with_type(self, type: record.ThreadType):
        self._type = type
        return self
    
    @async_chain.method
    async def with_member_id(self, id: int):
        self._members_id.append(id)
        return self
    
    @async_chain.method
    async def with_history(self, gen_func):
        gen = HistoryGen()
        gen = await gen_func(gen)
        self._history = await gen.get_result()
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.Thread(
            auto_archive_duration = self._auto_archive_duration,
            invitable = self._invitable,
            locked = self._locked,
            name = self._name,
            slowmode_delay = self._slowmode_delay,
            archived = self._archived,
            type = self._type,
            members_id = tuple(self._members_id),
            history = self._history
        )

class TextChannelGen:
    _default_auto_archive_duration : int
    _default_thread_slowmode_delay : int
    _name : str
    _nsfw : bool
    _slowmode_delay : int
    _threads : list[record.Thread]
    _topic : str
    _history : record.History

    def __init__(self):
        self._default_auto_archive_duration = 0
        self._default_thread_slowmode_delay = 0
        self._name = "default"
        self._nsfw = False
        self._slowmode_delay = 0
        self._threads = []
        self._topic = ""
        self._history = record.History(messages = ()) # is required
    
    @async_chain.method
    async def with_default_auto_archive_duration(self, val: int):
        self._default_auto_archive_duration = val
        return self
    
    @async_chain.method
    async def with_default_thread_slowmode_delay(self, val: int):
        self._default_thread_slowmode_delay = val
    
    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self

    @async_chain.method
    async def with_nsfw(self, nsfw: bool):
        self._nsfw = nsfw
        return self
    
    @async_chain.method
    async def with_slowmode_delay(self, slowmode_delay: int):
        self._slowmode_delay = slowmode_delay
        return self
    
    @async_chain.method
    async def with_topic(self, topic: str):
        self._topic = topic
        return self
    
    @async_chain.method
    async def with_history(self, gen_func):
        gen = HistoryGen()
        gen = await gen_func(gen)
        self._history = await gen.get_result()
        return self
    
    @async_chain.method
    async def with_thread(self, gen_func):
        gen = ThreadGen()
        gen = await gen_func(gen)
        self._threads.append(await gen.get_result())
        return self

    @async_chain.method
    async def get_result(self):
        return record.TextChannel(
            default_auto_archive_duration = self._default_auto_archive_duration,
            default_thread_slowmode_delay = self._default_thread_slowmode_delay,
            name = self._name,
            nsfw = self._nsfw,
            slowmode_delay = self._slowmode_delay,
            threads = tuple(self._threads),
            topic = self._topic,
            history = self._history
        )

DEFAULT_BITRATE = 64 * 1024 * 8

class VoiceChannelGen:
    _bitrate : int
    _name : str
    _slowmode_delay : int
    _user_limit : int
    _rtc_region : record.VoiceRegion
    _type : record.VoiceType
    _video_quality_mode : record.VideoQualityMode
    _history: record.History

    def __init__(self):
        self._bitrate = DEFAULT_BITRATE
        self._name = "default"
        self._slowmode_delay = 0
        self._user_limit =  25
        self._rtc_region = record.VoiceRegion.default
        self._type = record.VoiceType.voice
        self._video_quality_mode = record.VideoQualityMode.auto
        self._history = record.History(messages = ())
    
    @async_chain.method
    async def with_bitrate(self, bitrate: int):
        self._bitrate = bitrate
        return self
    
    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self
    
    @async_chain.method
    async def with_user_limit(self, limit: int):
        self._user_limit = limit
        return self
    
    @async_chain.method
    async def with_history(self, gen_func):
        gen = HistoryGen()
        gen = await gen_func(gen)
        self._history = await gen.get_result()
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.VoiceChannel(
            bitrate = self._bitrate,
            name = self._name,
            slowmode_delay = self._slowmode_delay,
            user_limit = self._user_limit,
            rtc_region = self._rtc_region,
            type = self._type,
            video_quality_mode = self._video_quality_mode,
            history = self._history
        )

from loguru import logger

class CategoryGen:
    _name : str
    _nsfw : bool
    _position : int
    _channels: list[record.TextChannel | record.VoiceChannel]

    def __init__(self):
        self._name = "default"
        self._nsfw = False
        self._position = 0
        self._channels = []

    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self

    @async_chain.method
    async def with_nsfw(self, nsfw: bool):
        self._nsfw = nsfw
        return self

    @async_chain.method
    async def with_position(self, position: int):
        self._position = position
        return self
    
    @async_chain.method
    async def with_text_channel(self, gen_func):
        gen = TextChannelGen()
        gen = await gen_func(gen)
        self._channels.append(await gen.get_result())
        return self
    
    @async_chain.method
    @logger.catch
    async def with_voice_channel(self, gen_func):
        gen = VoiceChannelGen()
        gen = await gen_func(gen)
        self._channels.append(await gen.get_result())
        return self

    @async_chain.method
    async def get_result(self):
        return record.Category(
            name = self._name,
            nsfw = self._nsfw,
            position = self._position,
            channels = self._channels
        )

class EmojiGen:
    _name : str
    _data : bytes

    def __init__(self):
        self._name = "default"
        # self._data is required

    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self

    @async_chain.method
    async def with_data(self, data: bytes):
        self._data = data
        return self

    @async_chain.method
    async def get_result(self):
        return record.Emoji(
            name = self._name,
            data = self._data
        )

class GuildGen:
    _name: str
    _emojis: list[record.Emoji]
    _categories: list[record.Category]
    _channels: list[record.TextChannel | record.VoiceChannel]

    def __init__(self):
        self._name = "default"
        self._emojis = []
        self._categories = []
        self._channels = []

    @async_chain.method
    async def with_name(self, name: str):
        self._name = name
        return self
    
    @async_chain.method
    async def with_emoji(self, gen_func):
        gen = EmojiGen()
        gen = await gen_func(gen)
        self._emojis.append(await gen.get_result())
        return self

    @async_chain.method
    async def with_category(self, gen_func):
        gen = CategoryGen()
        gen = await gen_func(gen)
        self._categories.append(await gen.get_result())
        return self
    
    @async_chain.method
    async def with_text_channel(self, gen_func):
        gen = TextChannelGen()
        gen = await gen_func(gen)
        self._channels.append(await gen.get_result())
        return self
    
    @async_chain.method
    async def with_voice_channel(self, gen_func):
        gen = VoiceChannelGen()
        gen = await gen_func(gen)
        self._channels.append(await gen.get_result())
        return self
    
    @async_chain.method
    async def get_result(self):
        return record.Guild(
            name = self._name,
            emojis = tuple(self._emojis),
            categories = tuple(self._categories),
            free_channels = tuple(self._channels)
        )
