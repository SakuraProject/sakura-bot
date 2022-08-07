# Sakura Bot

import os

from discord.ext import commands
import discord

from aiohttp import ClientSession
from dotenv import load_dotenv
from ujson import dumps
import aiomysql


load_dotenv()

bot = commands.Bot(command_prefix='sk!', intents=discord.Intents.all(), help_command=None, 
    allowed_mentions=discord.AllowedMentions.none())


@bot.listen()
async def on_ready():
    print("[Log]Hello " + bot.user.name)
    bot.session = ClientSession(loop=bot.loop, json_serialize=dumps)
    bot.Color = 0xffbdde
    await bot.load_extension("data.owners")
    await bot.load_extension("jishaku")
    print("[Log]Connecting MySQL")
    bot.pool = await aiomysql.create_pool(host=os.environ["MYSQLHOST"], port=int(os.environ["MYSQLPORT"]), user=os.environ["MYSQLUSER"], password=os.environ["MYSQLPASS"], db=os.environ["MYSQLDB"], loop=bot.loop, autocommit=True)
    for name in os.listdir("cmds"):
        if not name.startswith("."):
            try:
                await bot.load_extension("cmds."+name.replace(".py", ""))
            except Exception as e:
                print("[Log][err]" + str(e))
            else:
                print("[Log][load]" + name)
    print("[Log]Complete Booting,Thank you for using " + bot.user.name)

if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
