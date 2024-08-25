import asyncio
import os
import pickle
from pathlib import Path
import discord
import dotenv
from discord.ext import commands, tasks
from dpyConsole import Console
from rich import inspect
from enum import Enum, auto, StrEnum
import time

import record
import builder
from discord2record import conv_guild

import aiohttp
import requests

import gen_record

class ClearKind(StrEnum):
    ALL = auto()
    THREADS = auto()
    CHANNELS = auto()
    CATEGORIES = auto()
    EMOJIS = auto()


intents = discord.Intents.all()  # Подключаем "Разрешения"
intents.message_content = True
intents.members = True
intents.presences = True


bot = commands.Bot(command_prefix="!", intents=intents)  # Задаём префикс и интент
my_console = Console(bot)


#Эта шиза снизу для распознавания консолью всякой шизы вроде ClearKind
def path_convert(param):
    return Path(param)
my_console.converter.add_converter(Path, path_convert) # What the fuck?


def clear_kind_convert(param):
    return ClearKind(param)
my_console.converter.add_converter(ClearKind, clear_kind_convert) # What the fuck?


def dump(dtree):
    print(pickle.dumps(dtree))
    with open("tree.pkl", "wb") as file:
        pickle.dump(dtree, file)


@my_console.command()
async def create(guild: discord.Guild):
    
    start_time = time.time()
    print('ok')
    gen = gen_record.GuildGen()
    guild_obj = await (await conv_guild(guild, gen)).get_result()
    
    print(guild_obj)
    await asyncio.to_thread(dump, dtree=guild_obj)

    end_time = time.time()
    print("Create complete!")
    print(f"Время выполнения: {end_time-start_time} секунд")


@my_console.command()
async def clear(guild: discord.Guild, clear_kind: ClearKind = ClearKind.ALL):
    if clear_kind in {ClearKind.ALL, ClearKind.THREADS}:
        for thread in guild.threads:
            await thread.delete()
        print("Threads deletion is complete.")
    if clear_kind in {ClearKind.ALL, ClearKind.CHANNELS}:
        for channel in guild.channels:
            await channel.delete()
        print("Channels deletion is complete.")
    if clear_kind in {ClearKind.ALL, ClearKind.CATEGORIES}:
        for category in guild.categories:
            await category.delete()
        print("Categories deletion is complete.")
    if clear_kind in {ClearKind.ALL, ClearKind.EMOJIS}:
        for emoji in guild.emojis:
            await emoji.delete()
        print("Emojis deletion is complete.")


@my_console.command()
async def load(guild: discord.Guild, file_name: Path):
    with open(file_name, "rb") as file:
        guild_from_file = pickle.load(file)
    guild_builder = builder.GuildBuilder(guild_from_file, bot)
    await guild_builder.build(guild)
    print("Load complete!")

@my_console.command()
async def test_gen(guild: discord.Guild):
    async def msg1(gen):
        return (
            gen
            .with_content("Hello world!")
        )

    async def history(gen):
        return (
            gen
            .with_message(msg1)
        )
    async def chan(gen):
        return (
            gen
            .with_name("test_chan")
            .with_history(history)
        )
    async def category(gen):
        return (
            gen
            .with_name("test")
            .with_text_channel(chan)
        )
    print("start")
    guild_record = await (
        gen_record.GuildGen()
        .with_name("guild_name")
        .with_category(category)
    ).get_result()
    print("tree initilized!")
    print(guild_record)
    guild_builder = builder.GuildBuilder(guild_record, bot)
    await guild_builder.build(guild)
    print("test tree building complete!")

#Для проверки кусков кода, которые пугают Артёмов
@bot.command()
async def test(ctx):
    pass


dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
my_console.start()
bot.run(token)
