from os import listdir
import logging


async def setup(bot):
    for name in listdir("cogs/sakurabrand"):
        if not name.startswith(("_", ".")) and not name == "plugin.py":
            try:
                await bot.load_extension("cogs.sakurabrand." + name.replace(".py", ""))
            except Exception:
                logging.exception(f"Error on serverutil.{name}")
            else:
                print("[Log][load]" + name)
