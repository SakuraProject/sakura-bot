from discord.ext import commands
import discord
import os
import aiomysql
from dotenv import load_dotenv
from aiohttp import ClientSession
from ujson import dumps

load_dotenv()
intent=discord.Intents.all()
bot = commands.Bot(command_prefix='sk!',intents=intent)


@bot.listen()
async def on_ready():
  print("[Log]Hello " + bot.user.name)
  bot.session = ClientSession(loop=bot.loop, json_serialize=dumps)
  bot.Color = 0xffbdde
  await bot.load_extension("data.owners")
  await bot.load_extension("jishaku")
  print("[Log]Connecting MySQL")
  bot.pool = await aiomysql.create_pool(host=os.environ["MYSQLHOST"], port=int(os.environ["MYSQLPORT"]),user=os.environ["MYSQLUSER"], password=os.environ["MYSQLPASS"],db=os.environ["MYSQLDB"], loop=bot.loop,autocommit=True)
  for name in os.listdir("cmds"):
    if not name.startswith("."):
      try:
        await bot.load_extension("cmds."+name.replace(".py",""))
      except Exception as e:
        print("[Log][err]" + str(e))
      else:
        print("[Log][load]" + name)
  print("[Log]Complete Booting,Thank you for using " + bot.user.name)

bot.run(os.environ["TOKEN"])
