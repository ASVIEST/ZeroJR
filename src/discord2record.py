import discord
import gen_record
from dataclasses import dataclass

# class Indexer:
    # wrote_categories: []

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

class MessageConverter(Converter):
    def __init__(self, message: MessagePayload):
        self._message = message
    
    async def convert(self, gen):
        return await (
            gen
            .with_display_name(self._message.author.display_name)
            .with_display_avatar_url(self._message.author.display_avatar.url)
            .with_content(self._message.content)
        )

MAX_MESSAGE_LEN = 2000

class HistoryConverter(Converter):
    def __init__(self, history):
        self._history = history # save async iterator
    
    async def combine_messages(self, history):
        cnt = 0
        old_msg = ""
        old_author = None
    
        async for message in history:
            msg = message.content
            author = message.author
            len_ = len(msg)
            cnt = cnt + len_ + 1

            if (
                cnt <= MAX_MESSAGE_LEN and 
                old_author != None and 
                can_combine(old_author, author)
            ): msg = old_msg + '\n' + msg
            else:
                if old_author != None:
                  yield MessagePayload(old_msg, old_author)
                cnt = len_
            
            old_msg = msg
            old_author = author

        yield MessagePayload(msg, author)

    async def convert(self, gen):
        print("HistoryConverter")
        async for message in self.combine_messages(self._history):
            # if message.content != '':
            await gen.with_message(MessageConverter(message).gen_func)
        
        return gen

class ThreadConverter(Converter):
    def __init__(self, thread: discord.Thread):
        self._thread = thread
    
    async def convert(self, gen):
        print("ThreadConverter")
        await self._thread.fetch_members()
        print("fe")
        for member in self._thread.members:
            await gen.with_member_id(member.id)
        print("conv")
        return gen

class TextChannelConverter(Converter):
    def __init__(self, channel: discord.TextChannel):
        self._channel = channel
    
    async def convert(self, gen):
        print("TextChannelConverter")
        await (
            gen
            .with_name(self._channel.name)
            .with_nsfw(self._channel.nsfw)
            .with_history(HistoryConverter(self._channel.history(limit = None, oldest_first=True)).gen_func)
        )
        for thread in self._channel.threads:
            await gen.with_thread(ThreadConverter(thread).gen_func)
            print("ok")
        print("end")
        return gen

class CategoryConverter(Converter):
    def __init__(self, category: discord.CategoryChannel):
        self._category = category
    
    async def convert(self, gen):
        print("CONV")
        # print(self._category.nsfw)
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
        print("after chan")
        return gen

async def conv_message(message: discord.Message, gen: gen_record.MessageGen):
    return await (
        gen
        .with_display_name(message.author.display_name)
        .with_display_avatar_url(message.author.display_avatar.url)
        .with_content(message.content)
    )

# async def conv_text_channel()

async def conv_category(category: discord.CategoryChannel, gen: gen_record.CategoryGen):
    gen = await (
        gen
        .with_name(category.name)
        .with_nsfw(category.nsfw)
        .with_position(category.position)
    )

    for chan in category.channels:
        match chan:
          case discord.TextChannel(): print("text_channel")#gen.with_text_channel(lambda gen: await conv_text_channel(gen))
          case _: print("Invalid channel")
    
    return gen

async def conv_guild(guild: discord.Guild, gen: gen_record.GuildGen):
    for category in guild.categories:
        await gen.with_category(CategoryConverter(category).gen_func)
    
    return gen
