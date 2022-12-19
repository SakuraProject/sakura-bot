import discord
from discord.ext import commands
import speedtest
import asyncio
import time

from utils import Bot


class SpeedTest(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(description="botを動かしているサーバーの速度を計測します")
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    async def speedtest(self, ctx: commands.Context):
        msg = await ctx.send("計測中、しばらくお待ちください")
        stest = speedtest.Speedtest()
        await self.bot.loop.run_in_executor(None, stest.get_best_server)
        up = await self.bot.loop.run_in_executor(None, stest.upload)
        dl = await self.bot.loop.run_in_executor(None, stest.download)
        ebd = discord.Embed(
            title="speedtest",
            description=f"**ダウンロード**:\n{dl / 1024 / 1024}Mbps\n"
                        f"**アップロード**:\n{up / 1024 / 1024}Mbps"
        )
        await msg.edit(content="", embed=ebd)

    @commands.hybrid_command(description="botのpingを取得します")
    async def ping(self, ctx: commands.Context):
        sending = time.time()
        await ctx.send("計測中...")
        latency = self.bot.latency * 1000
        time_ = time.time()
        sock_ping = await self.bot.cogs["Websocket"].sock.ping()
        while not sock_ping.done():
            await asyncio.sleep(0.001)
        backend_latency = int((time.time() - time_) * 1000)

        embed = discord.Embed(
            title="ping",
            description="Botの動作速度に関する情報です。"
        ).add_field(
            name="Discordとの接続速度", value=f"{latency}ms"
        ).add_field(
            name="バックエンドとの通信速度", value=f"{backend_latency}ms"
        ).add_field(
            name="Discordへのメッセージ送信にかかった時間",
            value=f"{int((time.time() - sending) * 1000)}ms"
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(SpeedTest(bot))
