# Free RT - online Notice

from discord.ext import commands
from discord import app_commands
import discord

import asyncio
from orjson import loads

from utils import Bot, TryConverter, dumps


class OnlineNotice(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache: dict[int, list] = {}
        self.wait_cache: list[int] = []

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS OnlineNotice(
                UserId BIGINT PRIMARY KEY NOT NULL,
                Authors JSON
            );"""
        )
        cache = await self.bot.execute_sql(
            "SELECT * FROM OnlineNotice;", _return_type="fetchall"
        )
        self.cache = {c[0]: loads(c[1]) for c in cache}

    @commands.hybrid_group(description="ユーザーがオンラインになったときに通知します。")
    async def online_notice(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("使用方法が違います。")

    @online_notice.command(
        name="add", aliases=["set", "追加", "設定"],
        description="オンライン通知のユーザーを追加します。"
    )
    @app_commands.describe(notice_user="通知するユーザー")
    async def _add(
        self, ctx: commands.Context,
        notice_user: TryConverter[discord.Member, discord.User, discord.Object]
    ):
        self.cache.setdefault(notice_user.id, [])
        self.cache[notice_user.id].append(ctx.author.id)

        await self.bot.execute_sql(
            """INSERT INTO OnlineNotice VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE Authors=%s""",
            (notice_user.id, dumps(self.cache[notice_user.id]),
             dumps(self.cache[notice_user.id]))
        )
        await ctx.send("Ok")

    @online_notice.command(
        aliases=["delete", "del", "削除", "消去", "rem", "rm", "rmv"],
        description="オンライン通知のユーザーを削除します。"
    )
    async def remove(
        self, ctx: commands.Context,
        notice_user: TryConverter[discord.Member, discord.User, discord.Object]
    ):
        if (notice_user.id not in self.cache
                or ctx.author.id not in self.cache[notice_user.id]):
            return await ctx.send("そのユーザーは登録されていません。")

        self.cache[notice_user.id].remove(ctx.author.id)
        await self.bot.execute_sql(
            "UPDATE OnlineNotice SET Authors = %s WHERE UserId = %s;",
            (dumps(self.cache[notice_user.id]), notice_user.id)
        )

    # require: presence_intent

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.status == after.status:
            return
        if after.status != discord.Status.online:
            return
        if after.id in self.cache:
            return

        if self.cache.get(after.id):
            self.wait_cache.append(after.id)
            for id_ in self.cache[after.id]:
                try:
                    e = discord.Embed(
                        title="オンライン通知",
                        description=f"{after.mention}さんがオンラインになりました。"
                    )
                    user = self.bot.get_user(id_)
                    if not user:
                        del self.cache[after.id][self.cache[after.id].index(
                            id_)]
                        await self.bot.execute_sql(
                            "UPDATE OnlineNotice SET Authors = %s WHERE UserId = %s",
                            (dumps(self.cache[after.id]), after.id)
                        )
                        continue
                    await user.send(embed=e)
                except Exception:
                    pass
            await asyncio.sleep(1)
            self.wait_cache.remove(after.id)


async def setup(bot):
    await bot.add_cog(OnlineNotice(bot))
