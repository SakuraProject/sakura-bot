import discord
from discord.ext import commands
from speedtest import Speedtest

class speedtest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def speedtest(self,ctx):
        """
        NLang ja botサーバーのスピードテスト
        botを動かしているサーバーのスピードテストを実行します
        **使いかた：**
        EVAL self.bot.command_prefix+'speedtest'
        ELang ja
        NLang default speedtest for bot server
        speedtest for server to run bot
        **How to use：**
        EVAL self.bot.command_prefix+'speedtest'
        ELang default
        """
        msg = await ctx.send("計測中、しばらくお待ちください")
        stest = Speedtest()
        stest.get_best_server()
        up = await self.bot.loop.run_in_executor(None, stest.upload)
        dl = await self.bot.loop.run_in_executor(None, stest.download)
        ebd = discord.Embed(title="speedtest",description="**ダウンロード**:\n" + str(dl/1024/1024) + "Mbps\n**アップロード**:\n" + str(up/1024/1024) + "Mbps")
        await msg.edit(content="",embeds=[ebd])
        

async def setup(bot):
    await bot.add_cog(speedtest(bot))
