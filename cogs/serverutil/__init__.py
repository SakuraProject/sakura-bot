from logging import getLogger
from os import listdir

logger = getLogger(__name__)

async def setup(bot):
    for name in listdir("cogs/serverutil"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cogs.serverutil." + name.replace(".py", ""))
            except Exception as e:
                logger.exception(f"{name} failed to load. \n reason:{e}")
            else:
                logger.debug(f"{name} loaded.")
