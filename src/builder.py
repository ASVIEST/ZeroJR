from rich import inspect
import discord
from discord.ext import commands
import record
import asyncio
from loguru import logger

class CachedWebhookStorage:
    ## [TextChannel(id=1) webhook, TextChannel(id=2) webhook]
    ## max = 2 => +TextChannel(id=3) webhook, -TextChannel(id=2) webhook
    def __init__(self, max_count: int):
        self._max_count = max_count
        self._channel_to_webhook = {}
        self._webhook_cnt = 0
    
    async def compute_webhook_cnt(self, channel):
        if channel.id not in self._channel_to_webhook:
            self._webhook_cnt += len(await channel.webhooks()) # channel already have webhooks => add it to sum

    @logger.catch()
    async def acquire_webhook(self, channel: discord.TextChannel):
        await self.compute_webhook_cnt(channel)
        print(self._webhook_cnt)

        NAME = f"ШизаВебхуковая {channel.name}"
        webhook: discord.Webhook = None
        if self._webhook_cnt >= self._max_count:
            _, last_webhook = self._channel_to_webhook.popitem()
            await last_webhook.edit(
                channel = channel, 
                name=NAME,
                reason="Next channel"
            ) # create -> rate limit more common
            webhook = last_webhook
        else:
            webhook = await channel.create_webhook(name = NAME)
        
        self._webhook_cnt += 1
        self._channel_to_webhook[webhook.channel.id] = webhook
        return webhook
    
    async def release_webhooks(self):
        for webhook in self._channel_to_webhook.values():
            await webhook.delete()


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

    async def build(self, sender: discord.TextChannel | discord.Thread, webhook: discord.Webhook):
        print("MessageBuilder build()")
        async with sender.typing():
            have_thread = self.message.thread != None
            message = await webhook.send(
                self.message.content, 
                username = self.message.display_name, 
                avatar_url = self.message.display_avatar_url,
                wait = have_thread,
                thread = sender if isinstance(sender, discord.Thread) else MISSING
            )

            if have_thread:
                builder = ThreadBuilder(self.message.thread, self.webhooks, self.bot)
                await builder.build(message)


class HistoryBuilder(Builder):
    def __init__(self, history: record.History, webhooks: CachedWebhookStorage, bot: commands.Bot):
        self.bot = bot
        self.history = history
        self.webhooks = webhooks


    async def build(self, channel: discord.TextChannel | discord.VoiceChannel, sender: discord.TextChannel | discord.Thread | discord.VoiceChannel):
        print("HistoryBuilder build()")
        webhook = await self.webhooks.acquire_webhook(channel)
        for message in self.history.messages:
            inspect(message.content)
            builder = MessageBuilder(message, self.webhooks, self.bot)
            await builder.build(sender, webhook)

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
        await history_builder.build(channel, new_thread)

        # await new_thread.edit(** self.thread.as_dict())
        for user_id in self.thread.members_id:
            user = obj.guild.get_member(user_id)
            if user != None:
                await new_thread.add_user(user)

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
        await builder.build(new_voice_channel, new_voice_channel)

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
    
        for thread in self.channel.threads:
            builder = ThreadBuilder(thread, self.webhooks, self.bot)
            await builder.build(new_text_channel)
        
        builder = HistoryBuilder(self.channel.history, self.webhooks, self.bot)
        await builder.build(new_text_channel, new_text_channel)


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

        CHANNEL_BUILDER = {record.TextChannel: TextChannelBuilder,
                         record.VoiceChannel: VoiceChannelBuilder}

        for channel in self.category.channels:
            builder = CHANNEL_BUILDER[type(channel)](channel, self.webhooks, self.bot)
            await builder.build(guild, new_category_channel)

from dataclasses import asdict
class GuildBuilder(Builder):
    def __init__(self, guild: record.Guild, bot: commands.Bot):
        self.bot = bot
        self.guild = guild
        self.webhooks = CachedWebhookStorage(2)
    
    def _get_edits(self):
        return {"name": self.guild.name}

    async def build(self, guild: discord.Guild):
        print("GuildBuilder build()")
        await guild.edit(** self._get_edits())

        for emoji in self.guild.emojis:
            await guild.create_custom_emoji(name = emoji.name, image = emoji.data)

        for category in self.guild.categories:
            builder = CategoryBuilder(category, self.webhooks, self.bot)
            await builder.build(guild)
        
        await self.webhooks.release_webhooks()