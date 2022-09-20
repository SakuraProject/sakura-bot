# Sakura moderation commands

import discord
from discord.ext import commands

from pytimeparse.timeparse import timeparse
from datetime import timedelta


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def timeout(self, ctx, member: discord.Member, *, sec):
        sec = timeparse(sec)
        tdl = timedelta(seconds=sec)
        await member.timeout(
            tdl, reason=f"timeout command by {ctx.author}"
        )
        await ctx.send("Ok")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(
            None, reason=f"untimeout command by {ctx.author}"
        )
        await ctx.send("Ok")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User | discord.Object):
        try:
            await ctx.guild.unban(user)
        except discord.Forbidden:
            return await ctx.send("BAN解除に失敗しました。")
        await ctx.send("banを解除しました")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member):
        await member.kick()
        await ctx.send("kickしました")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.User | discord.Object):
        try:
            await ctx.guild.ban(user)
        except discord.Forbidden:
            return await ctx.send("BANに失敗しました。")
        await ctx.send("banしました。")


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
