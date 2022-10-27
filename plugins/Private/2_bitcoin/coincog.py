import ccxt
import discord

from cogs.sakurabrand.plugin import is_enable
from discord.ext import commands
from utils import Bot

class EncryptCoin(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @is_enable()
    @commands.group()
    async def encrypt_coin(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")


    @is_enable()
    @encrypt_coin.command()
    async def price(self, ctx):
        view = discord.ui.View()
        view.add_item(CoinList())
        await ctx.send(content="表示するコインを選んでください", view=view)


class CoinList(discord.ui.Select):
    def __init__(self):
        options = []
        coins = ["BTC/JPY|ビットコイン","ETH/JPY|イーサリアム","ETC/JPY|イーサリアムクラシック","XRP/JPY|リップル","MONA/JPY|モナコイン"]
        for coin in coins:
            options.append(discord.SelectOption(
                label=coin.split("|")[1], description=coin.split("|")[0], value=coin))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        coincheck = ccxt.coincheck()
        item = self.values[0].split("|")
        price = str(coincheck.fetch_ticker(symbol=item[0])["last"])
        interaction.response.send_message("現在の1" + item[1] + "の価格は" + price + "円です")
        
        
async def setup(bot: Bot):
    await bot.add_cog(EncryptCoin(bot))
