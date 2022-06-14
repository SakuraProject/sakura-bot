# Free RT - gamesearch

import discord
from discord.ext import commands

from urllib.parse import quote_plus
from ujson import loads


class GameSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["searchgame", "ゲームを探す"],
    )
    async def gamesearch(self, ctx, *, name: str):
        async with self.bot.session.get(
            "https://ysmsrv.wjg.jp/disbot/gamesearch.php?q=" + quote_plus(name, encoding='utf-8')
        ) as resp:
            gj = loads(await resp.text())
            hdw = ""
            try:
                game = gj["Items"][0]
                gametitle = game["Item"]["titleKana"]
                for item in gj["Items"]:
                    if gametitle in item["Item"]["titleKana"]:
                        hdw = hdw + " " + item["Item"]["hardware"]
            except IndexError:
                await ctx.send("すみません。見つかりませんでした。別の単語をお試しください")
            else:
                embed = discord.Embed(
                    title=gametitle + "の詳細",
                    description=game["Item"]["itemCaption"].replace('\\n', '\n'),
                    color=self.bot.Color
                )
                embed.add_field(name="機種", value=hdw)
                embed.set_image(url=game["Item"]["largeImageUrl"])
                embed.set_footer(text="ゲーム情報検索")
                await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GameSearch(bot))
