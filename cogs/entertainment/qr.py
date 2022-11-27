import os
import cv2
import discord
import pyqrcode
from discord.ext import commands

from utils import Bot


class qr(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(description="QRコード生成・読み取り機能")
    async def qr(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send("使用方法が違います。")

    @qr.command(description="QRコードをテキストから生成します")
    async def make(self, ctx: commands.Context, text: str):
        a = pyqrcode.create(content=text, error='H')
        a.png(file=str(ctx.author.id) + '.png', scale=6)
        await ctx.send(file=discord.File(str(ctx.author.id) + '.png'))
        os.remove(str(ctx.author.id) + '.png')

    @qr.command(description="QRコードを読み取ります")
    async def read(self, ctx: commands.Context, url: str | None = None):
        if url is None:
            if ctx.message.attachments[0].url:
                url = ctx.message.attachments[0].url
            elif ctx.message.attachments[0].url is None:
                return await ctx.send("画像がありません。")
        async with self.bot.session.get(url) as resp:
            with open(str(ctx.author.id) + 'r.png', 'wb') as fp:
                while True:
                    r = await resp.content.read(10)  # 4
                    if not r:
                        break
                    fp.write(r)
        image = cv2.imread(str(ctx.author.id) + 'r.png')
        qrDetector = cv2.QRCodeDetector()
        data, _, _ = qrDetector.detectAndDecode(image)
        await ctx.send(data)
        os.remove(str(ctx.author.id) + 'r.png')


async def setup(bot: Bot):
    await bot.add_cog(qr(bot))