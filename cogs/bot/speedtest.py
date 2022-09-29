import discord
from discord.ext import commands
from speedtest import Speedtest
import asyncio
import time


class speedtest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def speedtest(self, ctx):
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
        await self.bot.loop.run_in_executor(None, stest.get_best_server)
        up = await self.bot.loop.run_in_executor(None, stest.upload)
        dl = await self.bot.loop.run_in_executor(None, stest.download)
        ebd = discord.Embed(title="speedtest", description="**ダウンロード**:\n" +
                            str(dl / 1024 / 1024) + "Mbps\n**アップロード**:\n" + str(up / 1024 / 1024) + "Mbps")
        await msg.edit(content="", embeds=[ebd])

    @commands.command()
    async def ping(self, ctx):
        """
        NLang ja botのpingを取得します
        botのpingを取得します
        **使いかた：**
        EVAL self.bot.command_prefix+'ping'
        ELang ja
        NLang default get latency for bot
        get latency for bot
        **How to use：**
        EVAL self.bot.command_prefix+'ping'
        ELang default
        """
        p1 = self.bot.latency * 1000
        t = time.time()
        f = await self.bot.cogs["Websocket"].sock.ping()
        while not f.done():
            await asyncio.sleep(1 / 1000)
        p2 = int((time.time() - t) * 1000)
        ebd = discord.Embed(title="ping", description="**Discordとの接続速度**:\n" +
                            str(p1) + "ms\n**バックエンドとの通信速度**:\n" + str(p2) + "ms")
        await ctx.send(embeds=[ebd])


async def setup(bot):
    await bot.add_cog(speedtest(bot))
