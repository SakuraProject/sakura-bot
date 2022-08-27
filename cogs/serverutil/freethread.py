import discord
from discord.ext import commands


class freethread(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    @commands.group(
        aliases=["フリスレ", "ft"]
    )
    async def freethread(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("この機能を有効にするにはチャンネルトピックにフリスレと書いてください")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.TextChannel):
            if message.channel.topic != None:
                if message.channel.topic.find("フリスレ") != -1:
                    await message.create_thread(name=message.content)


async def setup(bot):
    await bot.add_cog(freethread(bot))
