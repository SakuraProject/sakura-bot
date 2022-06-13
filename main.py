from discord.ext import commands
import discord
import os
from dotenv import load_dotenv


load_dotenv()
intent=discord.Intents.all()
bot = commands.Bot(command_prefix='gm!',intents=intent)

bot.run(token=os.environ["TOKEN"])
