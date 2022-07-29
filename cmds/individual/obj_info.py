# Sakura bot - discord object Info commands

from discord.ext import commands
import discord


class ObjectInfo(commands.Cog):
    "discordのオブジェクト情報表示コマンドのコグです。"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    BADGES = {
        "UserFlags.verified_bot_developer": "<:verified_bot_developer:991964080292233306>",
        "UserFlags.early_supporter": "<:early_supporter:991963681502003230>",
        "UserFlags.staff": "<:discord_staff:991963642729869372>",
        "UserFlags.partner": "<:partnered_server_owner:991964149884137472>",
        "UserFlags.hypesquad": "<:discord_HypeSquad_disc:991962182604566639>",
        "UserFlags.bug_hunter": "<:bug_hunter:991963877770276944>",
        "UserFlags.hypesquad_bravery": "<:discord_hypesquad_bravery_disc:991962211641741392>",
        "UserFlags.hypesquad_brilliance": "<:discord_hypesquad_briliance_disc:991962274816331796>",
        "UserFlags.hypesquad_balance": "<:discord_hypesquad_balance_disc:991962200879157288>"
    }
    BOT = "<:discord_Bot_disc:991962236706885734>"
    VERIFIED_BOT = "<:verified_bot:991963186234413139>"


    @commands.command()
    async def userinfo(
        self, ctx: commands.Context, target: discord.Member | discord.User = commands.Author
    ):
        e = discord.Embed(
            title=f"{target}{'🤖' if target.bot else ''}の情報",
            description=f"ID: `{target.id}`"
        )
        await ctx.reply(embed=e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ObjectInfo(bot))
