# Sakura Bot - Welcome & Goodbye feature

from discord.ext import commands

from utils import Bot


class Welcome(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS Welcome(
                GuildId BIGINT PRIMARY KEY NOT NULL, Onoff BOOLEAN,
                Message TEXT, UserRole BIGINT, BotRole BIGINT
            );"""
        )

    @commands.group(description="入室時にメッセージを送ったりロールを付与する機能です。")
    async def welcome(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            return await ctx.send("使い方が違います。")

async def setup(bot: Bot) -> None:
    await bot.add_cog(Welcome(bot))
