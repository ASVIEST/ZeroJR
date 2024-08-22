import discord
intents = discord.Intents.default() # Подключаем "Разрешения"
intents.message_content = True
intents.members = True
intents.presences = True


from discord.ext import commands, tasks
bot = commands.Bot(command_prefix='!', intents=intents) # Задаём префикс и интенты


from dpyConsole import Console
my_console = Console(bot)


from datetime import datetime
def get_current_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S")

import pickle
def dump(dtree):
    print(pickle.dumps(dtree))
    with open('categorys_list.pkl', 'wb') as file: 
        pickle.dump(dtree, file) 

import record
from rich import inspect
import asyncio
@my_console.command()
async def array():
    tree = []
    for guild in bot.guilds:
        for category in guild.categories:
            inspect(record.Category(category))
            tree.append(record.Category(category))
            for channel in category.text_channels:
                inspect(channel)
    await asyncio.to_thread(dump, dtree = tree)


from colors import Colors
@bot.event
async def on_ready():
    print(f"{Colors.OKGREEN}INFO ({get_current_time()}):     BOT ONLINE!")


import dotenv
import os
dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
my_console.start()
bot.run(token)
