import discord
from discord.ext import commands

from utils import Bot, get_webhook


class Afk(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        ctsql = "create table if not exists afk (userid BIGINT, vl TEXT);"
        await self.bot.execute_sql(ctsql)
        res = await self.bot.execute_sql(
            "SELECT * FROM afk;", _return_type="fetchall"
        )
        self.cache = {row[0]: row[1] for row in res}

    @commands.hybrid_group(description="留守メッセージ機能です。")
    async def afk(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @afk.command(description="AFKを設定します。")
    async def set(self, ctx: commands.Context, *, reason: str):
        if str(ctx.author.id) in self.cache:
            return await ctx.send("すでに設定されています。")
        await self.bot.execute_sql(
            "INSERT INTO afk (userid, vl) VALUES (%s,%s)",
            (str(ctx.author.id), reason)
        )
        self.cache[str(ctx.author.id)] = reason
        await ctx.send("設定しました")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.TextChannel):
            return

        if str(message.author.id) in self.cache:
            await self.bot.execute_sql("DELETE FROM afk WHERE userid=%s;", (str(message.author.id),))
            del self.cache[str(message.author.id)]
            await message.channel.send('afkを解除しました', reference=message)

        for m in message.mentions:
            if str(m.id) in self.cache:
                webhook = await get_webhook(message.channel)
                await webhook.send(
                    self.cache[str(m.id)],
                    username=f"{m.name} - 留守メッセージ",
                    avatar_url=m.display_avatar.url
                )


async def setup(bot):
    await bot.add_cog(Afk(bot))
