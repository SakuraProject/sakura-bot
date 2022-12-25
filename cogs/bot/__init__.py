from os import listdir
from logging import getLogger

logger = getLogger(__name__)

async def setup(bot):
    for name in listdir("cogs/bot"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cogs.bot." + name.replace(".py", ""))
            except Exception as e:
                logger.exception(f"{name} failed to load. \n reason:{e}")
            else:
                logger.debug(f"{name} loaded.")
