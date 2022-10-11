from os import listdir
import logging


async def setup(bot):
    for name in listdir("cogs/bot"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cogs.bot." + name.replace(".py", ""))
            except Exception:
                logging.exception("Error on bot.%s", name)
            else:
                print("[Log][load]" + name)
