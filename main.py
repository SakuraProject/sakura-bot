# Sakura Bot

import os

import discord

from aiohttp import ClientSession
from dotenv import load_dotenv
from ujson import dumps
import aiomysql

from utils import Bot


load_dotenv()

bot = Bot(command_prefix='sk!', intents=discord.Intents.all(), help_command=None, 
    allowed_mentions=discord.AllowedMentions.none())


@bot.listen()
async def on_ready():
    print(f"[Log]Hello {bot.user}")
    bot.session = ClientSession(loop=bot.loop, json_serialize=dumps)
    await bot.load_extension("data.owners")
    await bot.load_extension("jishaku")
    print("[Log]Connecting MySQL")
    bot.pool = await aiomysql.create_pool(
        host=os.environ["MYSQLHOST"], port=int(os.environ["MYSQLPORT"]),
        user=os.environ["MYSQLUSER"], password=os.environ["MYSQLPASS"],
        db=os.environ["MYSQLDB"], loop=bot.loop, autocommit=True
    )
    for name in os.listdir("cogs"):
        if not name.startswith("."):
            try:
                await bot.load_extension("cogs."+name.replace(".py", ""))
            except Exception as e:
                print("[Log][err]" + str(e))
            else:
                print("[Log][load]" + name)
    print(f"[Log]Complete Booting,Thank you for using {bot.user}")


if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
