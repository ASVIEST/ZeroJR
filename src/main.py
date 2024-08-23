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

    category_list = []
    for category in guild.categories:
        category_obj = record.Category(category)
        await category_obj.avisitor(category)
        category_list.append(category_obj)
    await asyncio.to_thread(dump, dtree=(guild_obj, category_list))
    end_time = time.time()
    print("Create complete!")
    print(f"Время выполнения: {end_time-start_time} секунд")
    inspect(guild_obj)


@my_console.command()
async def clear(guild: discord.Guild, clear_kind: ClearKind = ClearKind.ALL):
    if clear_kind in {ClearKind.ALL, ClearKind.THREADS}:
        for thread in guild.threads:
            await thread.delete()
        print("Thread deletion is complete.")
    if clear_kind in {ClearKind.ALL, ClearKind.CHANNELS}:
        for channel in guild.channels:
            await channel.delete()
        print("Channel deletion is complete.")
    if clear_kind in {ClearKind.ALL, ClearKind.CATEGORIES}:
        for category in guild.categories:
            await category.delete()
        print("Category deletion is complete.")


@my_console.command()
async def load(guild: discord.Guild, file_name: Path):
    with open(file_name, "rb") as file:
        category_list = pickle.load(file)
    for category in category_list:
        category_builder = builder.CategoryBuilder(category, bot)
        await category_builder.build(guild)
    print("Load complete!")


#не смотри сюда.
@bot.command()
async def test(ctx):
    #for emoji in ctx.guild.emojis:
    #    inspect(requests.get(emoji.url).content)
    img = requests.get(ctx.guild.emojis[0].url).content
    await ctx.guild.create_custom_emoji(name = "Test", image = img)


dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
my_console.start()
bot.run(token)
