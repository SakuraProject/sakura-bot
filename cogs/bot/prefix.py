# Sakura bot - custom prefix

from discord.ext import commands

from utils import Bot


class Prefix(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def prefix(self, ctx: commands.Context):
        await ctx.send("準備中...")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Prefix(bot))