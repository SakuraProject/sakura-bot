from os import listdir
import logging


async def setup(bot):
    for name in listdir("cmds/bot"):
        if not name.startswith(("_", ".")):
            try:
                await bot.load_extension("cmds.bot."+name.replace(".py", ""))
            except Exception as e:
                logging.exception(f"Error on bot.{name}")
            else:
                print("[Log][load]" + name)
