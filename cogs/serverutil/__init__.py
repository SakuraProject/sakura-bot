import logging
from os import listdir


async def setup(bot):
    for name in listdir("cogs/serverutil"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cogs.serverutil." + name.replace(".py", ""))
            except Exception:
                logging.exception(f"Error on serverutil.{name}")
            else:
                print("[Log][load]" + name)
