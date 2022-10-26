# Sakura Bot - About

from inspect import cleandoc

from discord.ext import commands
import discord

from utils import Bot


ABOUT_SAKURA_BOT = cleandoc("""
    SakuraBotは`SakuraProject(旧FreeRT開発チーム)`によって開発された多機能botです。
    このBotを使うことでdiscord全体を明るく、楽しく、便利にすることを目指しています。
    もしあなたもこのBotに興味があればぜひ貢献をご検討ください。

    ・Github: https://github.com/SakuraProject/sakura-bot/
    ・公式サーバー: https://discord.gg/KW4CZvYMJg/
    ・公式サイト: https://sakura-bot.net/
""")


class BotAbout(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def about(self, ctx: commands.Context):
        embed = discord.Embed(
            title="SakuraBotについて",
            description=ABOUT_SAKURA_BOT
        )
        embed.add_field(name="ユーザー数", value=f"{len(self.bot.users)}ユーザー")
        embed.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}サーバー")
        embed.add_field(name="開発言語", value="Python (discord.py v2.0.1)")
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(BotAbout(bot))
