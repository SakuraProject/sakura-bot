# Sakura bot - Free Thread

import discord
from discord.ext import commands


class FreeThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        aliases=["フリスレ", "ft"]
    )
    async def freethread(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply(
                "この機能を有効にするにはチャンネルトピックに`sk>freethread`と書いてください"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.TextChannel):
            if message.channel.topic is not None:
                if "sk>freethread" in message.channel.topic:
                    await message.create_thread(name=message.content)


async def setup(bot):
    await bot.add_cog(FreeThread(bot))
