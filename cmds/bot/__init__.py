from os import listdir
import logging


async def setup(bot):
    for name in listdir("cmds/bot"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cmds.bot."+name.replace(".py", ""))
            except:
                logging.exception("Error on bot.%s", name)
            else:
                print("[Log][load]" + name)
