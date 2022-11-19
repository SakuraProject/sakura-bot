from discord.ext import commands
import discord
from orjson import loads
import urllib.parse
import asyncio

from utils import Bot


class mynews(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(description="みんなのニュース機能")
    async def mynews(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send("使用方法が違います。")

    async def input(self, ctx: commands.Context, q: str):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout=180.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break

    @mynews.command(description="ニュースを投稿します")
    async def post(self, ctx: commands.Context):
        await ctx.send("投稿を開始します")
        req = dict()
        req["did"] = str(ctx.author.id)
        req["diname"] = ctx.author.name + '#' + ctx.author.discriminator
        try:
            req["ti"] = (await self.input(ctx, "ニュースのタイトルを入力してください")).content
            req["val"] = (await self.input(ctx, "ニュースの本文を入力してください")).content
            await ctx.send("送信しています")
            async with self.bot.session.post(
                "http://ysmsrv.wjg.jp/news/sendbydiscord.php", data=req
            ) as resp:
                rpt = await resp.text()
                await ctx.send(rpt)
        except SyntaxError:
            await ctx.send("投稿をキャンセルしました")

    @mynews.command(description="ニュースを検索します")
    async def day(self, ctx: commands.Context, day: str):
        async with self.bot.session.get(
            "https://ysmsrv.wjg.jp/news/timebydiscord.php?input_date=",
            query=urllib.parse.quote_plus(day, encoding='utf-8')
        ) as resp:
            rpt = await resp.json()
            if rpt == []:
                await ctx.reply("すみません。何も見つかりませんでした。日付を確認してみてください。例:2022/07/10")
            else:
                gj = rpt
                vie = discord.ui.View()
                if len(gj) >= 25:
                    tmp = []
                    for g in gj:
                        if len(tmp) == 24:
                            vie.add_item(SearchList(tmp, self.bot))
                            tmp = []
                        tmp.append(g)
                    vie.add_item(SearchList(tmp, self.bot))
                else:
                    vie.add_item(SearchList(gj, self.bot))
                await ctx.send("見たい記事を選択してください", view=vie)

    @mynews.command(description="今日のニュースを表示します")
    async def today(self, ctx: commands.Context):
        async with self.bot.session.get("https://ysmsrv.wjg.jp/news/apitoday.php") as resp:
            rpt = await resp.text()
            if rpt == "[]":
                await ctx.reply("すみません。何も見つかりませんでした。もし投稿したいnewsがある場合はnews postコマンドで投稿できます")
            else:
                gj = loads(rpt)
                vie = discord.ui.View()
                if len(gj) >= 25:
                    tmp = []
                    for g in gj:
                        if len(tmp) == 24:
                            vie.add_item(SearchList(tmp, self.bot))
                            tmp = []
                        tmp.append(g)
                    vie.add_item(SearchList(tmp, self.bot))
                else:
                    vie.add_item(SearchList(gj, self.bot))
                await ctx.send("見たい記事を選択してください", view=vie)


async def getusername(userid: str, bot: Bot):
    async with bot.session.get("https://ysmsrv.wjg.jp/news/" + userid) as resp:
        rpt = await resp.text()
        return rpt


class SearchList(discord.ui.Select):
    def __init__(self, args: list[dict[str, str]], bot: Bot):
        self.its = args
        self.bot = bot
        options = []
        for item in args:
            item["title"] = item["title"] if not item["title"] == "" else "non title"
            options.append(discord.SelectOption(
                label=item["title"], description=''))

        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for item in self.its:
            if item["title"] == self.values[0]:
                ebd = discord.Embed(
                    title=item["title"], description=item["text"], color=self.bot.Color)
                ebd.add_field(name="投稿者", value=(await getusername(item["user"], self.bot)))
                await interaction.response.edit_message(embeds=[ebd])


async def setup(bot: Bot):
    await bot.add_cog(mynews(bot))
