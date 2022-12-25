# Sakura Bot

import os

import discord

from dotenv import load_dotenv
from orjson import loads
import aiomysql
from logging import getLogger, config

from utils import Bot


load_dotenv()

with open("data/logger_setting.json", "r") as f:
    log_conf = loads(f.read())

config.dictConfig(log_conf)

logger = getLogger(__name__)

bot = Bot(
    command_prefix='sk!', intents=discord.Intents.all(),
    help_command=None, allowed_mentions=discord.AllowedMentions.none()
)


@bot.listen()
async def on_ready():
    logger.info("System will be ready...")
    await bot.load_extension("data.owners")
    await bot.load_extension("jishaku")
    logger.debug("Connecting Database Server...")
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
                logger.error(f"{name} failed to load. \nreason:{e}")
            else:
                logger.debug(f"{name} is Loaded.")
    try:
        await bot.load_extension("cogs.sakurabrand.plugin")
    except Exception as e:
        logger.error(f"Plugin failed to load. \nreason:{e}")
    else:
        logger.debug("Plugin loaded")
    logger.info(f"All systems are fine. \nthank you for using {bot.user}")


if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
