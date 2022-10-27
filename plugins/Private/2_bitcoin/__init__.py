from cogs.sakurabrand.plugin import PluginManager
from utils import Bot


async def setup(bot: Bot, manager: PluginManager):
    await manager.load_extension("coincog")
