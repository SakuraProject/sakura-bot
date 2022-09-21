# Sakura moderation commands

import discord
from discord.ext import commands
from discord import app_commands

from pytimeparse.timeparse import timeparse
from datetime import timedelta

from utils import TryConverter, Bot


class Moderation(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(description="メンバーをタイムアウトします。")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="タイムアウトするメンバー", sec="タイムアウトする時間")
    async def timeout(
        self, ctx: commands.Context,
        member: discord.Member, *, sec
    ):
        sec = timeparse(sec)
        if not sec:
            return await ctx.reply("秒数の変換に失敗しました。")
        tdl = timedelta(seconds=sec)
        await member.timeout(
            tdl, reason=f"timeout command by {ctx.author}"
        )
        await ctx.reply("タイムアウトしました。")

    @commands.hybrid_command(description="メンバーのタイムアウトを解除します。")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="タイムアウトを解除するメンバー")
    async def untimeout(self, ctx: commands.Context, member: discord.Member):
        await member.timeout(
            None, reason=f"untimeout command by {ctx.author}"
        )
        await ctx.reply("タイムアウトしました。")

    @commands.hybrid_command(description="メンバーのBANを解除します。")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    @app_commands.describe(user="対象のユーザー", reason="BANを解除する理由")
    async def unban(
        self, ctx: commands.Context,
        user: TryConverter[discord.User, discord.Object],
        *, reason: str | None = None
    ):
        assert ctx.guild
        try:
            await ctx.guild.unban(
                user, reason=f"{reason}\nSakura Bot Unban Command by {ctx.author}"
            )
        except discord.Forbidden:
            return await ctx.reply("BAN解除に失敗しました。")
        await ctx.reply("banを解除しました。")

    @commands.hybrid_command(description="メンバーをキックします。")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="キックするメンバー", reason="キックする理由")
    async def kick(
        self, ctx: commands.Context, member: discord.Member,
        *, reason: str | None = None
    ):
        await member.kick(
            reason=f"{reason}\nSakura Bot Kick Command by {ctx.author}"
        )
        await ctx.reply("kickしました。")

    @commands.hybrid_command(description="メンバーをBANします。")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    @app_commands.describe(user="BANするユーザー", reason="BANする理由")
    async def ban(
        self, ctx: commands.Context,
        user: TryConverter[discord.User, discord.Object], *,
        reason: str | None = None
    ):
        assert ctx.guild
        try:
            await ctx.guild.ban(
                user, reason=f"{reason}\nSakura Bot Ban Command by {ctx.author}"
            )
        except discord.Forbidden:
            return await ctx.reply("BANに失敗しました。")
        await ctx.reply("banしました。")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Moderation(bot))
