# Gombot - gamesearch

import discord
from discord.ext import commands

from urllib.parse import quote_plus
from orjson import loads

from utils import Bot


class GameSearch(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command(
        aliases=["searchgame", "ゲームを探す"],
        description="ゲーム機を検索できます。"
    )
    async def gamesearch(self, ctx: commands.Context, *, name: str):
        async with self.bot.session.get(
            "https://ysmsrv.wjg.jp/disbot/gamesearch.php?q=" +
                quote_plus(name, encoding='utf-8')
        ) as resp:
            gj = loads(await resp.text())
        hdw = ""
        try:
            game = gj["Items"][0]
            gametitle = game["Item"]["titleKana"]
            for item in gj["Items"]:
                if gametitle in item["Item"]["titleKana"]:
                    hdw += " " + item["Item"]["hardware"]
        except IndexError:
            await ctx.send("すみません。見つかりませんでした。別の単語をお試しください")
        else:
            await ctx.send(embed=discord.Embed(
                title=gametitle + "の詳細",
                description=game["Item"]["itemCaption"].replace('\\n', '\n'),
                color=self.bot.Color
            ).add_field(
                name="機種", value=hdw
            ).set_image(
                url=game["Item"]["largeImageUrl"]
            ).set_footer(text="ゲーム情報検索"))


async def setup(bot):
    await bot.add_cog(GameSearch(bot))
