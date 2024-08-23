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

import aiohttp
import requests

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

    guild_obj = record.Guild(guild)
    await guild_obj.avisitor(guild)
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


#Для проверки кусков кода, которые пугают Артёмов
@bot.command()
async def test(ctx):
    pass


dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
my_console.start()
bot.run(token)
