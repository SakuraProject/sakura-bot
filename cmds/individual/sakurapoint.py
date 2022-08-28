# Sakura Point General System

import discord
from discord.ext import commands

from utils import Bot


class SakuraPoint(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        await self.bot.execute_sql(
            "CREATE TABLE if not exists SakuraPoint(UserID BIGINT, Point BIGINT);"
        )

    @commands.command()
    async def spoint(self, ctx: commands.Context, target: discord.User | None = None):
        if target and not self.bot.is_owner(ctx.author):
            raise commands.NotOwner()
        data = await self.bot.execute_sql(
            "SELECT Point FROM SakuraPoint WHERE UserID = %s;",
            ((target or ctx.author).id,), "fetchone"
        )
        if not data:
            return await ctx.send("あなたはまだ一度もSakuraPointを獲得したことがありません。")
        await ctx.send(f"あなたのポイント: {data[0]}ポイント")


async def setup(bot: Bot) -> None:
    await bot.add_cog(SakuraPoint(bot))
