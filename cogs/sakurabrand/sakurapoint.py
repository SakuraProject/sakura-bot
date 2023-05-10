# Sakura Point General System

from typing import Literal

import re
import asyncio
from datetime import datetime
from collections import defaultdict

import discord
from discord.ext import commands, tasks

from utils import Bot


class SakuraPoint(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.pattern = re.compile(
            "(https?://)?discord(.gg|.com/invite)/KW4CZvYMJg")
        self.url = re.compile(
            r"https://discord.com/(api/)?oauth2/authorize\?(.*&)?client_id=985852917489737728.*"
        )
        self.ad_cache = []
        self.cache = defaultdict[int, int](int)

    async def cog_load(self) -> None:
        await self.bot.execute_sql(
            """CREATE TABLE if not exists SakuraPoint(
                UserID BIGINT PRIMARY KEY NOT NULL, Point BIGINT
            );"""
        )
        data = await self.bot.execute_sql(
            "SELECT * FROM SakuraPoint;", _return_type="fetchall"
        )
        for i in data:
            self.cache[i[0]] = i[1]

        self.point_task.start()

    @commands.command()
    async def spoint(self, ctx: commands.Context, target: discord.User | None = None):
        if target and not await self.bot.is_owner(ctx.author):
            raise commands.NotOwner()
        data = self.cache.get((target or ctx.author).id)
        if not data:
            return await ctx.send("あなたはまだ一度もSakuraPointを獲得したことがありません。")
        await ctx.send(f"あなたのポイント: {data}ポイント")

    @commands.command()
    @commands.is_owner()
    async def spmanage(
        self, ctx: commands.Context, mode: Literal["add", "remove"],
        target: discord.User, amount: int
    ):
        amount = (mode == "add" or -1) * amount
        await self.spmanage_(target, amount)
        await ctx.send("Ok.")

    async def spmanage_(self, target: discord.abc.Snowflake, amount: int) -> None:
        await self.bot.execute_sql(
            """INSERT INTO SakuraPoint (UserId, Point) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE Point = Point + %s;""",
            (target.id, amount, amount)
        )
        self.cache[target.id] += amount

    def spcheck(self, user_id: int, min_point: int = 1) -> bool:
        "ユーザーがmin_point以上sakurapointを持っているかをチェックする。"
        if user_id not in self.cache:
            return False
        elif self.cache[user_id] < min_point:
            return False
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.TextChannel):
            return
        assert message.guild
        if message.author.bot:
            return
        if not (self.url.search(message.content)
                or self.pattern.search(message.content)):
            return
        content = "宣伝ありがとうございます！"
        if message.guild.id not in self.ad_cache:
            content += "\n300ポイントを獲得しました！"
            await self.bot.execute_sql(
                """INSERT INTO SakuraPoint (UserId, Point) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE Point = Point + %s;""",
                (message.author.id, 300, 300)
            )
            self.cache[message.author.id] += 300
        try:
            await message.channel.send(content, delete_after=3)
        except Exception:
            pass
        if message.guild.id not in self.ad_cache:
            self.ad_cache.append(message.guild.id)
            await asyncio.sleep(3600)
            self.ad_cache.remove(message.guild.id)

    @tasks.loop(hours=1)
    async def point_task(self):
        "ポイントを毎週削除する自動タスクです。"
        if not (datetime.now().weekday() == 0 and datetime.now().hour == 0):
            return
        # 月曜の午前0時台
        # Sakura Ad
        for user_id in self.bot.cogs["SakuraAd"].cache.keys():
            if not (user := self.bot.get_user(user_id)):
                del self.bot.cogs["SakuraAd"].cache[user_id]
                continue
            # 引き落とし額の決定
            amount = 300
            for am in self.bot.cogs["SakuraAd"].cache[user_id].values():
                amount += 100 + int(len(am) * 0.7)
            if user_id in self.bot.cogs["SakuraAd"].invisible_cache:
                amount += 200
            await self.spmanage_(user, amount)
            if self.cache[user_id] < 0:
                await user.send(embed=discord.Embed(
                    title="警告通知",
                    description=(
                        "SakuraAd機能にて引き落としを行ったところ、あなたのSakuraPointが0を下回りました。\n"
                        "毎週月曜日の0時の引き落としは続きますが、新たなSakuraAdの作成などはできなくなるためご注意ください。"
                    )
                ))


async def setup(bot: Bot) -> None:
    await bot.add_cog(SakuraPoint(bot))
