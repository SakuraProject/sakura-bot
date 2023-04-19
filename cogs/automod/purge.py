import discord
from discord.ext import commands

from utils import Bot


class Purge(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(description="メッセージを一斉削除します。")
    async def purge(
        self, ctx: commands.Context, length=0, target: discord.User | None = None
    ):
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("このコマンドはテキストチャンネルでしか実行できません。")
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
                if target is not None:
                    return m.author.id == target.id and m.id in [
                        ml.id for ml in mlis]
                else:
                    return m.id in [ml.id for ml in mlis]
            dmsg = await ctx.channel.purge(limit=100000, check=check)
            await ctx.send(str(len(dmsg)) + "メッセージを削除しました")
        else:
            dmsg = await ctx.channel.purge(
                limit=min(length, 300), check=lambda m: target is None or m.id == target.id
            )
            await ctx.send(str(len(dmsg)) + "メッセージを削除しました")


async def setup(bot: Bot):
    await bot.add_cog(Purge(bot))
