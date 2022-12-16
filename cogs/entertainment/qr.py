import os
import cv2
import discord
import qrcode
from discord.ext import commands
from io import BytesIO

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
        buffer = BytesIO()
        qr = qrcode.make(text)
        qr.save(buffer)
        buffer.seek(0)
        file = discord.File(buffer, "output_image.png")
        await ctx.reply(file=file)

    @qr.command(description="QRコードを読み取ります")
    async def read(self, ctx: commands.Context, url: str | None = None):
        if url is None:
            if ctx.message.attachments:
                url = ctx.message.attachments[0].url
            else:
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
        print(data)
        await ctx.send(data)
        os.remove(str(ctx.author.id) + 'r.png')


async def setup(bot: Bot):
    await bot.add_cog(qr(bot))