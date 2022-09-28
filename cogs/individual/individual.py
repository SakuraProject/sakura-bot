# sakura bot - individual (個人用コマンド全般)

from typing import Literal

import random

from discord.ext import commands
from discord import app_commands
import discord

from utils import Bot


class Individual(commands.Cog):
    ignore_bot_cache: list[int]

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self):
        await self.bot.execute_sql(
            "CREATE TABLE IF NOT EXISTS IgnoreFindBot"
            "(UserId BIGINT PRIMARY KEY NOT NULL)"
        )
        ifbc = await self.bot.execute_sql(
            "SELECT * FROM IgnoreFindBot",
            _return_type="fetchall"
        )
        self.ignore_bot_cache = list(bc[0] for bc in ifbc) if ifbc else []

    @commands.hybrid_command(description="指定された文字を話します。")
    @app_commands.describe(content="話す内容")
    async def say(self, ctx: commands.Context, content: str):
        await ctx.send(content)

    @commands.hybrid_command(description="サーバーにいない新しいbotを探します。")
    @app_commands.describe(condition="探す条件です。")
    @commands.guild_only()
    async def findnewbot(
        self, ctx: commands.Context,
        condition: Literal["online", "include_ignored"] | None = None
    ):
        assert ctx.guild

        bots = [
            u for u in self.bot.users
            if u.bot and u not in ctx.guild.members
            and (m.status != discord.Status.offline
                 if (m := u.mutual_guilds[0].get_member(u.id)) and condition == "online"
                 else True)
            and (u.id not in self.ignore_bot_cache
                 if condition != "include_ignored" else True)
        ]
        bot = random.choice(bots)
        await ctx.send(f"{bot}が見つかりました。(全{len(bots)}bot)", embed=discord.Embed(
            title="Bot Invite Link (permission 0)",
            description=discord.utils.oauth_url(bot.id, guild=ctx.guild)
        ))

    @commands.command()
    @commands.is_owner()
    async def manage_fnb(self, ctx: commands.Context, mode, id_: int):
        if mode == "add":
            if id_ in self.ignore_bot_cache:
                return await ctx.send("もういる。")
            self.ignore_bot_cache.append(id_)
            await self.bot.execute_sql(
                "INSERT INTO IgnoreFindBot VALUES %s",
                (id_,)
            )
        elif mode == "remove":
            if id_ not in self.ignore_bot_cache:
                return await ctx.send("そんなbotないよ。")
            self.ignore_bot_cache.remove(id_)
            await self.bot.execute_sql(
                "DELETE FROM IgnoreFindBot WHERE UserId = %s;",
                (id_,)
            )
        elif mode == "sync":
            for bot_id in self.ignore_bot_cache:
                if not self.bot.get_user(bot_id):
                    self.ignore_bot_cache.remove(bot_id)
                    await self.bot.execute_sql(
                        "DELETE FROM IgnoreFindBot WHERE UserId = %s;",
                        (bot_id,)
                    )
        else:
            return await ctx.send("そんなモードない。")
        await ctx.send("Ok")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Individual(bot))
