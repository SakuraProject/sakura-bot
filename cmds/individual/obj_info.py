# sakura bot - discord object Info commands

from discord.ext import commands


class ObjectInfo(commands.Cog):
    "discordのオブジェクト情報表示コマンドでのコグです。"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ObjectInfo(bot))
