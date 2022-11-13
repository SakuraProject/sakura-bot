import discord
from discord.ext import commands

from utils import Bot


class purge(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def purge(
        self, ctx: commands.Context, length=0, member: discord.User | None = None
    ):
        if length == 0:
            mlis = []
            inn = False
            async for m in ctx.channel.history(limit=100000):
                r = [getattr(e.emoji, "name", e.emoji) for e in m.reactions]
                if "wastebasket" in r or "🗑️" in r:
                    mlis.append(m)
                    if inn:
                        break
                    else:
                        inn = True
                else:
                    if inn:
                        mlis.append(m)

            def check(m):
                if member is not None:
                    return m.author.id == member.id and m.id in [
                        ml.id for ml in mlis]
                else:
                    return m.id in [ml.id for ml in mlis]
            dmsg = await ctx.channel.purge(limit=100000, check=check)
            await ctx.send(str(len(dmsg)) + "メッセージを削除しました")
        else:
            def check(m):
                if member is not None:
                    return m.author.id == member.id and m.id in [
                        ml.id for ml in mlis]
                else:
                    return True
            dmsg = await ctx.channel.purge(limit=length, check=check)
            await ctx.send(str(len(dmsg)) + "メッセージを削除しました")


async def setup(bot: Bot):
    await bot.add_cog(purge(bot))
