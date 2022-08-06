# Sakura bot - discord object Info commands

from discord.ext import commands
import discord

from utils import Bot


PERMISSIONS = {
    "administrator": "管理者",
    "view_audit_log": "監査ログを表示",
    "manage_guild": "サーバーの管理",
    "manage_roles": "ロールの管理",
    "manage_channels": "チャンネルの管理",
    "kick_members": "メンバーをキック",
    "ban_members": "メンバーをBAN",
    "create_instant_invite": "招待を作成",
    "change_nickname": "ニックネームの変更",
    "manage_nicknames": "ニックネームの管理",
    "manage_emojis": "絵文字の管理",
    "manage_webhooks": "ウェブフックの管理",
    "manage_events": "イベントの管理",
    "manage_threads": "スレッドの管理",
    "use_slash_commands": "スラッシュコマンドの使用",
    "view_guild_insights": "テキストチャンネルの閲覧＆ボイスチャンネルの表示",
    "send_messages": "メッセージを送信",
    "send_tts_messages": "TTSメッセージを送信",
    "manage_messages": "メッセージの管理",
    "embed_links": "埋め込みリンク",
    "attach_files": "ファイルを添付",
    "read_message_history": "メッセージ履歴を読む",
    "mention_everyone": "@everyone、@here、全てのロールにメンション",
    "external_emojis": "外部の絵文字の使用",
    "add_reactions": "リアクションの追加"
}


class EmbedSelect(discord.ui.Select):
    def __init__(self, embeds: list[discord.Embed]):
        self.embeds = embeds
        options = [discord.SelectOption(
            label=e.title or "...", description=e.description or "...", value=str(count)
        ) for count, e in enumerate(embeds)]

        super().__init__(placeholder='見たい項目を選んでください...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embeds[int(self.value)])


class EmbedsView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()

        self.add_item(EmbedSelect(embeds))


class ObjectInfo(commands.Cog):
    "discordのオブジェクト情報表示コマンドのコグです。"

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    BADGES = {
        "verified_bot_developer": "<:verified_bot_developer:991964080292233306>",
        "early_supporter": "<:early_supporter:991963681502003230>",
        "staff": "<:discord_staff:991963642729869372>",
        "partner": "<:partnered_server_owner:991964149884137472>",
        "hypesquad": "<:discord_HypeSquad_disc:991962182604566639>",
        "bug_hunter": "<:bug_hunter:991963877770276944>",
        "hypesquad_bravery": "<:discord_hypesquad_bravery_disc:991962211641741392>",
        "hypesquad_brilliance": "<:discord_hypesquad_briliance_disc:991962274816331796>",
        "hypesquad_balance": "<:discord_hypesquad_balance_disc:991962200879157288>"
    }
    BOT_EMOJI = "<:discord_Bot_disc:991962236706885734>"
    VERIFIED_BOT_EMOJI = "<:verified_bot:991963186234413139>"

    @commands.command(aliases=("ui2", "lookup", "user", "ユーザー情報"))
    async def userinfo2(
        self, ctx: commands.Context, target: discord.Member | discord.User = commands.Author
    ):
        badge = ""
        if target.public_flags.verified_bot:
            badge = self.VERIFIED_BOT_EMOJI
        elif target.bot:
            badge = self.BOT_EMOJI

        badge += "".join(self.BADGES.get(str(flg)[10:], "") for flg in target.public_flags.all())

        embed = discord.Embed(
            title=f"{target}{badge}の情報",
            description=f"ID: `{target.id}`"
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="アカウント作成日",
            value=discord.utils.format_dt(target.created_at)
        )
        if target.avatar is not None:
            embed.add_field(name="アイコンurl", value=target.avatar.url)

        if isinstance(target, discord.Member):
            if target.guild_avatar is not None:
                embed.add_field(
                    name="このサーバーでのアイコンurl",
                    value=target.guild_avatar.url
                )
            if target.display_name != target.name:
                embed.add_field(name="表示名", value=target.display_name)
            embed.add_field(
                name="サーバーへの参加日",
                value=discord.utils.format_dt(target.joined_at) if target.joined_at else "不明"
            )

        await ctx.reply(embed=embed)

    @commands.command()
    async def serverinfo(
        self, ctx: commands.Context, target: discord.Guild = commands.CurrentGuild
    ):
        embed = discord.Embed(
            title=f"{target.name}の情報",
            description=f"ID: `{target.id}`",
            color=self.bot.Color
        )
        embed.add_field(
            name="サーバー作成日時",
            value=discord.utils.format_dt(target.created_at)
        )
        embed.add_field(
            name="総チャンネル数 (カテゴリ数, ボイスチャンネル数, テキストチャンネル数)",
            value=f"`{len(target.channels)}` (`"
                  f"{sum(isinstance(c, discord.CategoryChannel) for c in target.channels)}`, "
                  f"`{len(target.voice_channels)}`, `{len(target.text_channels)}`)"
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(ObjectInfo(bot))
