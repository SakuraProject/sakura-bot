# Sakura bot - custom prefix

from typing import Literal

from discord.ext import commands
from aiomysql import Cursor

from utils import Bot


class Prefix(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def prepare_table(self, cursor: Cursor) -> tuple[
        tuple[tuple[int, str], ...], tuple[tuple[int, str], ...]
    ]:
        await cursor.execute("""CREATE TABLE IF NOT EXISTS UserPrefix(
            UserId BIGINT PRIMARY KEY NOT NULL, Prefix TEXT
        );""")
        await cursor.execute("""CREATE TABLE IF NOT EXISTS GuildPrefix(
            GuildId BIGINT PRIMARY KEY NOT NULL, Prefix TEXT
        );""")
        await cursor.execute("""SELECT * FROM UserPrefix;""")
        data1 = await cursor.fetchall()
        await cursor.execute("""SELECT * FROM GuildPrefix;""")
        return (data1, await cursor.fetchall())

    async def cog_load(self):
        "テーブルの準備とキャッシュの用意をする。"
        (users, guilds) = await self.bot.execute_sql(self.prepare_table)
        for (user_id, prefix) in users:
            self.bot.user_prefixes[user_id] = prefix
        for (guild_id, prefix) in guilds:
            self.bot.guild_prefixes[guild_id] = prefix

    @commands.hybrid_command(description="カスタムprefixを設定します。")
    async def prefix(
        self, ctx: commands.Context, mode: Literal["user", "server"], prefix: str
    ):
        if mode == "user":
            self.bot.user_prefixes[ctx.author.id] = prefix
            await self.bot.execute_sql(
                """INSERT INTO UserPrefix VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE Prefix=VALUES(Prefix);""",
                (ctx.author.id, prefix)
            )
        elif not ctx.guild:
            return await ctx.send("サーバーprefixの設定はDMで実行しないでください。")
        else:
            self.bot.guild_prefixes[ctx.guild.id] = prefix
            await self.bot.execute_sql(
                """INSERT INTO GuildPrefix VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE Prefix=VALUES(Prefix);""",
                (ctx.guild.id, prefix)
            )
        await ctx.send("Ok")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Prefix(bot))
