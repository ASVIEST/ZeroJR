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


@my_console.command()
async def hey(user: discord.User):
    print(f"Sending message to {user.name} id: = {user.id}")
    await user.send(f"Hello from Console! Im {bot.user.name}")


@tasks.loop(seconds=10)
async def process():
    channel = bot.get_channel(1247682726505611267)
    await channel.send('Example message')


from colors import Colors
@bot.event
async def on_ready():
    process.start()
    print(f"{Colors.OKGREEN}INFO ({get_current_time()}):     BOT ONLINE!")

    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f'{guild}, {channel}')


@bot.command()
async def dir_(ctx):
    print(dir(discord.errors))
    await ctx.send(dir(discord.errors))


@bot.command(pass_context=True)
async def nick(ctx, member: discord.Member, nickname):
    await member.edit(nick=nickname)

@nick.error
async def nick_error(error, ctx):
    await error.channel.send(ctx)


import dotenv
import os
dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
my_console.start()
bot.run(token)
