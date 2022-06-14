from os import listdir
import traceback


async def setup(bot):
  for name in listdir("cmds/individual"):
    if not name.startswith("."):
      try:
        await bot.load_extension(name.replace(".py",""))
      except Exception as e:
        print("[Log][err]" + str(e))
      else:
        print("[Log][load]" + name)
