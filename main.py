from discord.ext import commands
import os
from dotenv import load_dotenv


load_dotenv()

bot = commands.Bot(commands_prefix='gm!')

bot.run(token=os.environ["TOKEN"])