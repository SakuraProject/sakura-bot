# Sakura bot - discord object Info commands

from discord.ext import commands
import discord

from utils import Bot, EmbedsView


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
    BOT_EMOJI = "<:bot1:795159827318964284><:bot2:795160390400868402>"
    VERIFIED_BOT_EMOJI = "<:verified_bot:991963186234413139>"

    @commands.command(aliases=("ui", "lookup", "user", "ユーザー情報"))
    async def userinfo(
        self, ctx: commands.Context, target: discord.Member | discord.User = commands.Author
    ):
        """
        NLang ja ユーザー情報を表示するコマンドです
        ユーザー情報を表示するコマンドです
        **使いかた：**
        EVAL self.bot.command_prefix+'userinfo ユーザーid'
        EVAL self.bot.command_prefix+'userinfo'
        ELang ja
        NLang default Sorry, this command only supports Japanese.
        Sorry, this command only supports Japanese.
        ELang default
        """
        embeds = [
            self.create_ui_embed_1(target)
        ]
        if isinstance(target, discord.Member):
            embeds.append(self.create_ui_embed_2(target))
        if ctx.author.id in self.bot.owner_ids:
            embeds.append(self.create_ui_embed_3(target))

        if len(embeds) == 1:
            return await ctx.send(embed=embeds[0])
        await ctx.reply(embed=embeds[0], view=EmbedsView(embeds))

    # User info Embed creator

    def create_ui_embed_1(self, target: discord.User | discord.Member):
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
        return embed

    def create_ui_embed_2(self, target: discord.Member) -> discord.Embed:
        "権限一覧(メンバー専用)"
        desc = "\n".join(
            (":white_check_mark: " if getattr(target.guild_permissions, perm, False) else ":x:") + name
            for perm, name in PERMISSIONS.items()
        )
        embed = discord.Embed(
            title=f"{target}の権限",
            description=desc
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        return embed

    def create_ui_embed_3(self, target: discord.Member | discord.User) -> discord.Embed:
        "管理者用: 共通サーバー一覧"
        embed = discord.Embed(
            title=f"{target}の共通サーバー一覧",
            description="\n".join(
                f"{guild.name} ({guild.id})" for guild in target.mutual_guilds
            ) or "なし"
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        return embed


    @commands.command()
    async def serverinfo(
        self, ctx: commands.Context, target: discord.Guild = commands.CurrentGuild
    ):
        """
        NLang ja サーバー情報を表示するコマンドです
        サーバー情報を表示するコマンドです
        **使いかた：**
        EVAL self.bot.command_prefix+'serverinfo ユーザーid'
        EVAL self.bot.command_prefix+'serverinfo'
        ELang ja
        NLang default Sorry, this command only supports Japanese.
        Sorry, this command only supports Japanese.
        ELang default
        """
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
