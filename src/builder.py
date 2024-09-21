from rich import inspect
import discord
from discord.ext import commands
import record
import asyncio
from loguru import logger
from typing import Self
import aiohttp

class CachedWebhookStorage:
    ## [TextChannel(id=1) webhook, TextChannel(id=2) webhook]
    ## max = 2 => +TextChannel(id=3) webhook, -TextChannel(id=2) webhook
    def __init__(self, max_count: int):
        self._max_count = max_count
        self._channel_to_webhook = dict()
        self._webhook_id_to_channel = dict()
        self._webhook_edits: dict[int, int] = {}
        
    @logger.catch()
    def minimal_ratelimit_risk_webhook(self):
        filtered = {
            id: edits
            for id, edits in self._webhook_edits.items()
            if id in self._webhook_id_to_channel
        }
        if len(filtered) > 0:
            return min(filtered.items(), key=lambda x: x[1])[0]
        else:
            print("FILTERED LEN = 0")
            return tuple(self._webhook_id_to_channel.keys())[0]
        
    @property
    def _webhook_cnt(self):
        return len(self._channel_to_webhook)

    @logger.catch()
    async def acquire_webhook_impl(self, channel: discord.TextChannel):
        NAME = f"ШизаВебхуковая {channel.name}"
        webhook: discord.Webhook = None
        if self._webhook_cnt >= self._max_count:
            best_key = self.minimal_ratelimit_risk_webhook()           
            old_webhook_channel = self._webhook_id_to_channel.pop(best_key)
            old_webhook = self._channel_to_webhook.pop(old_webhook_channel)

            await old_webhook.edit(
                channel = channel, 
                name=NAME,
                reason="Next channel"
            ) # create -> rate limit more common
            webhook = old_webhook
            self._webhook_edits[webhook.id] += 1
        else:
            webhook = await channel.create_webhook(name = NAME)
            self._webhook_edits[webhook.id] = 0
        
        self._channel_to_webhook[webhook.channel.id] = webhook
        self._webhook_id_to_channel[webhook.id] = webhook.channel.id
        return webhook

    @logger.catch()
    async def acquire_webhook(self, sender: discord.TextChannel | discord.VoiceChannel | discord.Thread):
        channel = sender.parent if isinstance(sender, discord.Thread) else sender
        if channel.id in self._channel_to_webhook:
            return self._channel_to_webhook[channel.id]
        else:
            return await self.acquire_webhook_impl(channel)
    
    async def release_webhooks(self):
        for channel, webhook in self._channel_to_webhook.copy().items():
            await webhook.delete()
            del self._channel_to_webhook[channel]
            del self._webhook_id_to_channel[webhook.id]

class SendMessageTask:
    def __init__(self, sender: discord.TextChannel | discord.Thread, message: record.Message) -> None:
        self.sender = sender
        self.message = message
        self.dummies = [] # -> flatten
    
    @logger.catch()
    async def eval(self, webhooks: CachedWebhookStorage):
        print(f"SendMessageTask(sender={self.sender.name}) eval()")
        if not self.message.content.strip():
            return "Skip empty message"
        else:
            print(self.message.content)

        webhook = await webhooks.acquire_webhook(self.sender)
        async with self.sender.typing():
            have_thread = self.message.thread != None
            message = await webhook.send(
                self.message.content, 
                username = self.message.display_name, 
                avatar_url = self.message.display_avatar_url,
                wait = have_thread,
                thread = self.sender if isinstance(self.sender, discord.Thread) else MISSING
            )

            if have_thread:
                builder = ThreadBuilder(self.message.thread, webhooks, None) # XXX hack: bot = None; bot field not realy need
                self.dummies.append(await builder.build(message))

class BuildDummy:
    ## record.Server -> hierarchy visit -> dummy.eval()
    ## basic primitive some task (currently only message send task)
    ## and it can make useful things on it
    def __init__(self) -> None:
        self.message_send_tasks: dict[int, list[SendMessageTask]] = {}
    
    def with_send_message_task(self, task: SendMessageTask) -> Self:
        if task.sender.id not in self.message_send_tasks:
            self.message_send_tasks[task.sender.id] = [task]
        else:
            self.message_send_tasks[task.sender.id].append(task)

        return self
    
    @logger.catch()
    def __iadd__(self, other: Self):
        for channel in other.message_send_tasks.keys():
            self.message_send_tasks.setdefault(channel, [])
            self.message_send_tasks[channel] += \
                other.message_send_tasks[channel]
        return self
    
    def flatten_messages(self):
        for channel in self.message_send_tasks.keys():
            for i in range(len(self.message_send_tasks[channel])):
                for dummy in self.message_send_tasks[channel][i].dummies:
                    self += dummy
                    print(dummy)
                self.message_send_tasks[channel][i].dummies = []
    
    @logger.catch()
    def reorder_messages(self):
        iterators = [iter(it) for it in self.message_send_tasks.values()]
        while iterators:
            i = 0
            while i < len(iterators):
                try:
                    yield next(iterators[i])
                except StopIteration:
                    del iterators[i]
                i += 1

    async def eval(self, webhooks: CachedWebhookStorage):
        print("BuildDummy eval()")
        self.flatten_messages()
        for i in self.reorder_messages():
            await i.eval(webhooks)
        await webhooks.release_webhooks()

# Для чего я создан?
# Вызвать ошибку.
# Боже мой...
class Builder:
    bot: commands.Bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build(self, guild: discord.Guild):
        raise NotImplementedError("СОСАТЬ БОБРА! В дочернем классе builder'а нет функции build()!")

from discord.utils import MISSING

class MessageBuilder(Builder):
    def __init__(self, message: record.Message, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.message = message
        self.webhooks = webhooks
        
    @logger.catch()
    async def build(self, sender: discord.TextChannel | discord.Thread):
        print("MessageBuilder build()")
        return BuildDummy().with_send_message_task(
            SendMessageTask(sender, self.message)
        )

class HistoryBuilder(Builder):
    def __init__(self, history: record.History, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.history = history
        self.webhooks = webhooks


    async def build(self, channel: discord.TextChannel | discord.VoiceChannel, sender: discord.TextChannel | discord.Thread | discord.VoiceChannel):
        print("HistoryBuilder build()")
        dummy = BuildDummy()
        for message in self.history.messages:
            inspect(message.content)
            builder = MessageBuilder(message, self.webhooks, self.bot)
            dummy += await builder.build(sender)
        return dummy

class ThreadBuilder(Builder):
    def __init__(self, thread: record.Thread, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.webhooks = webhooks
        self.thread = thread

    async def build(self, obj: discord.TextChannel | discord.Message):
        print("ThreadBuilder build()")
        match obj:
            case discord.TextChannel(): 
                new_thread = await obj.create_thread(
                    name = self.thread.name,
                    type = discord.ChannelType(self.thread.type.value)
                )
                channel = obj
            case discord.Message():
                new_thread = await obj.create_thread(name = self.thread.name)
                channel = obj.channel
            case _: print("Unexpected object type for generating thread")
        
        history_builder = HistoryBuilder(self.thread.history, self.webhooks, self.bot)
        dummy = await history_builder.build(channel, new_thread)

        # await new_thread.edit(** self.thread.as_dict())
        for user_id in self.thread.members_id:
            user = obj.guild.get_member(user_id)
            if user != None:
                await new_thread.add_user(user)
        
        return dummy

class VoiceChannelBuilder(Builder):
    def __init__(self, channel: record.VoiceChannel, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.channel = channel
        self.webhooks = webhooks
    
    def _get_edits(self):
        d = asdict(self.channel)
        USED = {
            # nothing currently
        }
        return {key: d[key] for key in USED}

    async def build(self, guild: discord.Guild, category: discord.CategoryChannel):
        print("VoiceChannelBuilder build()")
        new_voice_channel = await guild.create_voice_channel(self.channel.name, category = category) #type = discord.ChannelType(self.channel.type.value))
        # await new_voice_channel.edit(** self.channel.as_dict())
        builder = HistoryBuilder(self.channel.history, self.webhooks, self.bot)
        dummy = await builder.build(new_voice_channel, new_voice_channel)
        return dummy

class TextChannelBuilder(Builder):
    def __init__(self, channel: record.TextChannel, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.channel = channel
        self.webhooks = webhooks
    
    def _get_edits(self):
        d = asdict(self.guild)
        USED = {
            "default_auto_archive_duration",
            "default_thread_slowmode_delay",
            "nsfw",
            "slowmode_delay",
            "topic"
        }
        return {key: d[key] for key in USED}


    async def build(self, guild: discord.Guild, category: discord.CategoryChannel):
        print("TextChannelBuilder build()")
        new_text_channel = await guild.create_text_channel(self.channel.name, category = category)
        # await new_text_channel.edit(** self._get_edits())

        dummy = BuildDummy()
        for thread in self.channel.threads:
            builder = ThreadBuilder(thread, self.webhooks, self.bot)
            dummy += await builder.build(new_text_channel)
        
        builder = HistoryBuilder(self.channel.history, self.webhooks, self.bot)
        dummy += await builder.build(new_text_channel, new_text_channel)
        return dummy

CHANNEL_BUILDER = {
    record.TextChannel: TextChannelBuilder,
    record.VoiceChannel: VoiceChannelBuilder
}

class CategoryBuilder(Builder):
    def __init__(self, category: record.Category, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.category = category
        self.webhooks = webhooks

    def _get_edits(self):
        return {"nsfw": self.guild.nsfw}


    async def build(self, guild: discord.Guild):
        print("CategoryBuilder build()")
        # Если Дискорд начнёт умирать - убери position из класса Категории.
        # Оно работает, не трогай...
        new_category_channel = await guild.create_category_channel(self.category.name, position = self.category.position)
        # await new_category_channel.edit(** self.category.as_dict())

        dummy = BuildDummy()
        for channel in self.category.channels:
            builder = CHANNEL_BUILDER[type(channel)](channel, self.webhooks, self.bot)
            dummy += await builder.build(guild, new_category_channel)
        return dummy

from dataclasses import asdict
class GuildBuilder(Builder):
    def __init__(self, guild: record.Guild, bot: commands.Bot):
        self.bot = bot
        self.guild = guild
        self.webhooks = CachedWebhookStorage(10)
    
    def _get_edits(self):
        return {"name": self.guild.name}
    
    @logger.catch()
    async def build(self, guild: discord.Guild):
        print("GuildBuilder build()")
        await guild.edit(** self._get_edits())

        for emoji in self.guild.emojis:
            await guild.create_custom_emoji(name = emoji.name, image = emoji.data)

        for category in self.guild.categories:
            builder = CategoryBuilder(category, self.webhooks, self.bot)
            dummy = await builder.build(guild)
            await dummy.eval(self.webhooks)
        
        for channel in self.guild.free_channels:
            builder = CHANNEL_BUILDER[type(channel)](channel, self.webhooks, self.bot)
            dummy = await builder.build(guild, None)
            await dummy.eval(self.webhooks)
        