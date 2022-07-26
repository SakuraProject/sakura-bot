# Sakura bot - discord object Info commands

from discord.ext import commands
import discord


class ObjectInfo(commands.Cog):
    "discordのオブジェクト情報表示コマンドのコグです。"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def userinfo(self, ctx: commands.Context, target: discord.User):
        e = discord.Embed(
            title=f"{target}{'🤖' if target.bot else ''}の情報",
            description=f"ID: `{target.id}`"
        )
        await ctx.reply(embed=e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ObjectInfo(bot))
