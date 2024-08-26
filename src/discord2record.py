import discord
import gen_record
from dataclasses import dataclass
import aiohttp

class Converter:
    async def convert(self, gen):
        raise NotImplementedError("convert")
    
    @property
    def gen_func(self):
        async def wrapper(gen):
            return await self.convert(gen)
        return wrapper

@dataclass
class MessagePayload:
    content: str
    author: discord.Member
    thread: discord.Thread | None = None

@dataclass(eq = True)
class MessageAuthorPayload:
    id: int

    # может быть один пользователь (или webhook), 
    # который поменял аватарку или имя на сервере,
    # тогда это должно быть в разных сообщениях
    display_name: str
    display_avatar_url: str

def message_author_payload(author: discord.Member):
    return MessageAuthorPayload(
        author.id,
        author.display_name,
        author.display_avatar.url
    )

def can_combine(a: discord.Member, b: discord.Member):
    return message_author_payload(a) == message_author_payload(b)

class ThreadConverter(Converter):
    def __init__(self, thread: discord.Thread):
        self._thread = thread
    
    async def convert(self, gen):
        print("ThreadConverter")
        await self._thread.fetch_members()
        await (
            gen
            .with_name(self._thread.name)
        )
        for member in self._thread.members:
            await gen.with_member_id(member.id)
        
        return gen

class MessageConverter(Converter):
    def __init__(self, message: MessagePayload):
        self._message = message
    
    async def convert(self, gen):
        await (
            gen
            .with_display_name(self._message.author.display_name)
            .with_display_avatar_url(self._message.author.display_avatar.url)
            .with_content(self._message.content)
        )

        if self._message.thread != None:
            await gen.with_thread(ThreadConverter(self._message.thread).gen_func)
        
        return gen

MAX_MESSAGE_LEN = 2000

class HistoryConverter(Converter):
    def __init__(self, history):
        self._history = history # save async iterator
    
    async def skip_channel_thread_messages(self, history):
        # discord history может видеть некоторые системные сообщения, 
        # например, потоки без связанных сообщений,
        # это мешает создать правильное дерево
        async for message in history:
            if message.type != discord.MessageType.thread_created:
                yield message

    async def combine_messages(self, history):
        cnt = 0
        old_msg = ""
        old_author = None
    
        async for message in history:
            msg = message.content
            author = message.author
            thread = message.thread
            len_ = len(msg)
            cnt = cnt + len_ + 1
            
            if (
                cnt <= MAX_MESSAGE_LEN and
                old_author != None and 
                thread == None and
                can_combine(old_author, author)
            ): msg = old_msg + '\n' + msg
            else:
                if old_author != None:
                  yield MessagePayload(old_msg, old_author, old_thread)
                cnt = len_
            
            old_msg = msg
            old_author = author
            old_thread = thread

        yield MessagePayload(msg, author, thread)
    
    async def skip_empty_messages(self, history):
        async for message in history:
            if message.content != '':
                yield message

    async def convert(self, gen):
        print("HistoryConverter")
        async for message in self.skip_empty_messages(self.combine_messages(self.skip_channel_thread_messages(self._history))):
            await gen.with_message(MessageConverter(message).gen_func)
        
        return gen


class TextChannelConverter(Converter):
    def __init__(self, channel: discord.TextChannel):
        self._channel = channel
    
    async def _is_message_thread(self, thread: discord.Thread):
        # thread.starting_message не работает, 
        # поэтому кажется, что это единственный способ проверить его 
        # (если только не проверять все сообщения на наличие свойства thread)
        try:
            msg = await self._channel.fetch_message(thread.id)
            if msg.type == discord.MessageType.thread_created:
                return False
            else:
                return True
        except discord.NotFound:
            return False

    async def convert(self, gen):
        print("TextChannelConverter")
        await (
            gen
            .with_name(self._channel.name)
            .with_nsfw(self._channel.nsfw)
            .with_history(HistoryConverter(self._channel.history(limit = None, oldest_first=True)).gen_func)
        )
        for thread in self._channel.threads:
            if not(await self._is_message_thread(thread)):
                print(thread.starting_message)
                await gen.with_thread(ThreadConverter(thread).gen_func)
        return gen

class CategoryConverter(Converter):
    def __init__(self, category: discord.CategoryChannel):
        self._category = category
    
    async def convert(self, gen):
        await (
            gen
            .with_name(self._category.name)
            .with_nsfw(self._category.nsfw)
            .with_position(self._category.position)
        )

        for channel in self._category.channels:
            match channel:
                case discord.TextChannel(): await gen.with_text_channel(TextChannelConverter(channel).gen_func)
                case discord.VoiceChannel: print("voice_channel")
        return gen

class EmojiConverter(Converter):
    def __init__(self, emoji: discord.Emoji):
        self._emoji = emoji
    
    async def convert(self, gen):
        await (
            gen
            .with_name(self._emoji.name)
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(self._emoji.url) as resp:
                await gen.with_data(await resp.read())

        return gen


class GuildConverter(Converter):
    def __init__(self, guild: discord.Guild):
        self._guild = guild
    
    async def convert(self, gen):
        await (
            gen
            .with_name(self._guild.name)
        )

        for emoji in self._guild.emojis:
            await gen.with_emoji(EmojiConverter(emoji).gen_func)

        for category in self._guild.categories:
            await gen.with_category(CategoryConverter(category).gen_func)

        return gen
