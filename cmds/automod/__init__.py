from os import listdir
import traceback


async def setup(bot):
  for name in listdir("cmds/automod"):
    if not name.startswith(("_",".")):
      try:
        await bot.load_extension("cmds.automod."+name.replace(".py",""))
      except Exception as e:
        print("[Log][err]" + str(e))
      else:
        print("[Log][load]" + name)