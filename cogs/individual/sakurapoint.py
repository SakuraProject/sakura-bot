# Sakura Point General System

from typing import Literal

import re
import asyncio

import discord
from discord.ext import commands

from utils import Bot


class SakuraPoint(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.pattern = re.compile("(https?://)?discord(.gg|.com/invite)/.{6,}")
        self.url = re.compile(
            f'https://discord.com/oauth2/authorize\\?client_id={bot.user.id}'
            ".*"
        )
        self.ad_cache = []

    async def cog_load(self) -> None:
        await self.bot.execute_sql(
            """CREATE TABLE if not exists SakuraPoint(
                UserID BIGINT PRIMARY KEY NOT NULL, Point BIGINT
            );"""
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

    @commands.command()
    @commands.is_owner()
    async def spmanage(
        self, ctx: commands.Context, mode: Literal["add", "remove"],
        target: discord.User, amount: int
    ):
        amount = (mode == "add" or -1) * amount
        await self.bot.execute_sql(
            """INSERT INTO SakuraPoint (UserId, Point) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE Point = VALUES(Point) + %s;""",
            (target.id, amount, amount)
        )
        await ctx.send("Ok.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.TextChannel):
            return
        if message.author.bot:
            return
        if not ("discord.gg/freert" in message.content or self.url.search(message.content)):
            return
        content = "宣伝ありがとうございます！"
        if not message.guild.id in self.ad_cache:
            content += "\n1000ポイントを獲得しました！"
            await self.bot.execute_sql(
                """INSERT INTO SakuraPoint (UserId, Point) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE Point = VALUES(Point) + %s;""",
                (message.author.id, 1000, 1000)
            )
        try:
            await message.channel.send(content, delete_after=3)
        except:
            pass
        if not message.guild.id in self.ad_cache:
            self.ad_cache.append(message.guild.id)
            await asyncio.sleep(3600)
            self.ad_cache.remove(message.guild.id)


async def setup(bot: Bot) -> None:
    await bot.add_cog(SakuraPoint(bot))
