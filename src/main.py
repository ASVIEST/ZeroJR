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
from discord2record import GuildConverter

import aiohttp
import requests

import gen_record

# import uvloop
# uvloop.install()


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
    gen = gen_record.GuildGen()
    gen = await GuildConverter(guild).convert(gen)
    guild_obj = await gen.get_result()

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



def alambda(fn):
    async def wrapper(gen):
        return await fn(gen)
    return wrapper

@my_console.command()
async def test_gen(guild: discord.Guild):
    print("start")
    guild_record = await (
        gen_record.GuildGen()
        .with_name("guild_name")
        .with_category(alambda(lambda gen: (
            gen
            .with_name("test_category")
            .with_text_channel(alambda(lambda gen: (
                gen
                .with_name("test_chan")
                .with_history(alambda(lambda gen: (
                    gen
                    .with_message(alambda(lambda gen: (
                        gen
                        .with_content("Hello world!")
                    )))
                )))
            )))
        )))
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
