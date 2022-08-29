from os import listdir
import logging


async def setup(bot):
    for name in listdir("cmds/individual"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cmds.individual."+name.replace(".py", ""))
            except:
                logging.exception(f"Error on individual.{name}")
            else:
                print("[Log][load]" + name)
