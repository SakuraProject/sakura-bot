from os import listdir
import logging


async def setup(bot):
    for name in listdir("cogs/entertainment"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cogs.entertainment."+name.replace(".py", ""))
            except:
                logging.exception(f"Error on entertainment.{name}")
            else:
                print("[Log][load]" + name)
