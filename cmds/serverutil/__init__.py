from os import listdir
import logging


async def setup(bot):
    for name in listdir("cmds/serverutil"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cmds.serverutil."+name.replace(".py", ""))
            except:
                logging.exception(f"Error on serverutil.{name}")
            else:
                print("[Log][load]" + name)
