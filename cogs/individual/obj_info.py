# Sakura bot - discord object Info commands

from discord.ext import commands
import discord

from utils import Bot, EmbedsView
from data import sakurabadge
from data.permissions import PERMISSIONS


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

    @commands.hybrid_command(
        aliases=("ui", "lookup", "user", "ユーザー情報"), description="ユーザー情報を表示します。"
    )
    async def userinfo(
        self, ctx: commands.Context, target: discord.Member | discord.User = commands.Author
    ):
        embeds = [
            self.create_ui_embed_1(target)
        ]
        if isinstance(target, discord.Member):
            embeds.append(self.create_ui_embed_2(target))
        if ctx.author.id in self.bot.owner_ids:
            embeds.append(self.create_ui_embed_3(target))

        view = EmbedsView(embeds)
        await view.send(ctx)

    # User info Embed creator

    def create_ui_embed_1(self, target: discord.User | discord.Member):
        badge = ""
        if target.public_flags.verified_bot:
            badge = self.VERIFIED_BOT_EMOJI
        elif target.bot:
            badge = self.BOT_EMOJI

        badge += "".join(self.BADGES.get(str(flg)[10:], "")
                         for flg in target.public_flags.all())

        embed = discord.Embed(
            title=f"{target}の情報",
            description="基本情報です。"
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(name="ID", value=str(target.id))
        embed.add_field(name="バッジ", value=badge or "なし")
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
                value=discord.utils.format_dt(
                    target.joined_at) if target.joined_at else "不明"
            )
        return embed

    def create_ui_embed_2(self, target: discord.Member) -> discord.Embed:
        "権限一覧(メンバー専用)"
        desc = "\n".join(
            (":white_check_mark: " if getattr(
                target.guild_permissions, perm, False) else ":x:") + name
            for perm, name in PERMISSIONS.items()
        )

        return discord.Embed(
            title=f"{target}の権限",
            description=desc
        ).set_footer(
            text="このサーバー全体での権限です。"
        ).set_thumbnail(url=target.display_avatar.url)

    def create_ui_embed_3(self, target: discord.Member |
                          discord.User) -> discord.Embed:
        "管理者用: 共通サーバー一覧"
        embed = discord.Embed(
            title=f"{target}の共通サーバー一覧",
            description="(管理者専用)"
        )
        if isinstance(target, discord.ClientUser):
            embed.add_field(name="** **", value="全サーバー")
            return embed
        embed.add_field(
            name="** **",
            value="\n".join(
                f"{guild.name} ({guild.id})" for guild in target.mutual_guilds
            ) or "なし"
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        return embed

    def create_ui_embed_4(self, target: discord.Member |
                          discord.User) -> discord.Embed:
        "Sakuraバッヂ用"
        embed = discord.Embed(
            title="Sakura Badge 一覧",
            description="その人が持っているSakuraバッヂの一覧です。"
        )
        badges = (sakurabadge.BADGES[i] for i in
                  sakurabadge.get_badge(target, self.bot))
        embed.add_field(name="** **", value="\n".join(
            f"{i['emoji']}{i['name']}: {i['description']}"
            for i in badges
        )[:1000])
        return embed

    @commands.hybrid_command(
        aliases=("si", "server", "サーバー情報"), description="サーバー情報を表示します。"
    )
    async def serverinfo(
        self, ctx: commands.Context, target: discord.Guild = commands.CurrentGuild
    ):
        embeds = [self.create_si_embed_1(target)]
        descriptions = {"基本情報": "サーバーの基本情報です。"}
        if target == ctx.guild:
            embeds.append(self.create_si_embed_2(target))
            descriptions["ロール一覧"] = "サーバーにあるロールの一覧です。"
            embeds.append(self.create_si_embed_3(target))
            descriptions["古参メンバーランキング"] = "このサーバーに最も古くからいるメンバーから順番に表示します。"

        view = EmbedsView(embeds, descriptions)
        await view.send(ctx)

    # Server info Embed creator

    def create_si_embed_1(self, target: discord.Guild) -> discord.Embed:
        "基本情報"
        embed = discord.Embed(
            title=f"{target.name}の情報",
            description=f"ID: `{target.id}`",
            color=self.bot.Color
        )
        if target.icon:
            embed.set_thumbnail(url=target.icon.url)

        embed.add_field(
            name="サーバー作成日時",
            value=discord.utils.format_dt(target.created_at)
        )
        if target.owner:
            embed.add_field(
                name="オーナー", value=f"{target.owner} ({target.owner.id})")

        embed.add_field(
            name="チャンネル数 (カテゴリ, テキスト, ボイス, ステージ)",
            value=f"`{len(target.channels)}` (`"
                  f"{len(target.categories)}`, `{len(target.voice_channels)}`, "
                  f"`{len(target.text_channels)}`, `{len(target.stage_channels)}`)"
        )
        embed.add_field(
            name="ユーザー数(通常ユーザー, bot)",
            value=f"`{len(target.members)}` (`{sum(not m.bot for m in target.members)}"
                  f"`, `{sum(m.bot for m in target.members)}`)"
        )
        return embed

    def create_si_embed_2(self, target: discord.Guild) -> discord.Embed:
        "ロール一覧(そのサーバー限定)"
        desc = "\n".join(
            f"{r.name if r.name == 'everyone' else r.mention}"
            f"({r.id}): {len(r.members)}人"
            for r in sorted(target.roles, key=lambda r: r.position, reverse=True)
        )
        embed = discord.Embed(
            title="ロール一覧",
            description=desc[:4090] + "\n..." if len(desc) > 4095 else desc
        )
        return embed

    def create_si_embed_3(self, target: discord.Guild) -> discord.Embed:
        "古参ランキング(そのサーバー限定)"
        desc = "\n".join(
            f"{m.mention}: {discord.utils.format_dt(m.joined_at or discord.utils.utcnow())}"
            f"({(discord.utils.utcnow() - (m.joined_at or discord.utils.utcnow())).days}日前)"
            for m in sorted(target.members, key=lambda m: m.joined_at or discord.utils.utcnow())
        )
        embed = discord.Embed(
            title="古参メンバーランキング",
            description=desc[:4090] + "\n..." if len(desc) > 4095 else desc
        )
        return embed

    @commands.hybrid_command(description="絵文字の情報を表示します。")
    async def emojiinfo(self, ctx: commands.Context, target: discord.Emoji):
        embed = discord.Embed(
            title=f"{target}の情報",
            description=f"ID: `{target.id}`",
            color=self.bot.Color
        )
        embed.set_image(url=target.url)
        embed.add_field(
            name="絵文字作成日時",
            value=discord.utils.format_dt(target.created_at)
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="招待リンクの情報を表示します。")
    async def inviteinfo(self, ctx: commands.Context, target: discord.Invite):
        embed = discord.Embed(
            title=f"{target}の情報",
            description=f"ID: `{target.id}`",
            color=self.bot.Color
        ).add_field(
            name="作成日時",
            value=discord.utils.format_dt(target.created_at)
                  if target.created_at else "なし"
        ).add_field(
            name="有効期限",
            value=discord.utils.format_dt(target.expires_at)
                  if target.expires_at else "不明"
        ).add_field(
            name="使用回数", value=target.uses
        ).add_field(
            name="使用可能回数", value=target.max_uses
        ).add_field(
            name="招待リンクの使用可能回数が制限されているか",
            value="はい" if target.max_uses is None else "いいえ"
        )
        await ctx.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(ObjectInfo(bot))
