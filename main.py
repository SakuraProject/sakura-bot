from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
from aiohttp import ClientSession
from ujson import dumps

load_dotenv()
intent=discord.Intents.all()
bot = commands.Bot(command_prefix='gm!',intents=intent)


@bot.listen()
async def on_ready():
  print("[Log]Hello " + bot.user.name)
  for name in os.listdir("cmds"):
    if not name.startswith("."):
      try:
        await bot.load_extension("cmds."+name.replace(".py",""))
      except Exception as e:
        print("[Log][err]" + str(e))
      else:
        print("[Log][load]" + name)
  bot.session = ClientSession(loop=bot.loop, json_serialize=dumps)
  bot.Color = 0xffbdde
  print("[Log]Complete Booting,Thank you for using " + bot.user.name)

bot.run(os.environ["TOKEN"])
