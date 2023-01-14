# Sakura Bot - Welcome & Goodbye feature

from typing import Literal

from discord.ext import commands
import discord

from utils import Bot, GuildContext
from data import emojis


class Welcome(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS Welcome(
                GuildId BIGINT PRIMARY KEY NOT NULL, Onoff BOOLEAN, Channel BIGINT,
                Message TEXT, UserRole BIGINT DEFAULT 0, BotRole BIGINT DEFAULT 0
            );"""
        )
        self.guilds_cache: list[int] = []
        lis = await self.bot.execute_sql(
            "SELECT GuildId FROM Welcome WHERE OnOff = 1;", _return_type="fetchall"
        )
        self.guilds_cache = [row[0] for row in lis]

    @commands.hybrid_group(
        description="入退室時の機能", fallback="settings"
    )
    @commands.guild_only()
    async def welcome(self, ctx: GuildContext):
        if ctx.invoked_subcommand:
            return
        if ctx.guild.id not in self.guilds_cache:
            return await ctx.send(embed=discord.Embed(
                title="入退室機能 - 設定状況", description=f"{emojis.INFO}設定されていません。",
                color=0xff0000
            ))

        def get_channel_ment(channel_id: int) -> str:
            if (ch := self.bot.get_channel(channel_id)):
                return ch.mention
            return f"{emojis.WARNING}存在しないチャンネル"

        def get_role_ment(role_id: int) -> str:
            if (role := ctx.guild.get_role(role_id)):
                return role.mention
            return f"{emojis.WARNING}存在しないロールが指定されています。"

        (row,) = await self.bot.execute_sql(
            "SELECT * FROM Welcome WHERE GuildId = %s LIMIT 1;",
            (ctx.guild.id,), _return_type="fetchone"
        )
        await ctx.send(embed=discord.Embed(
            title="入退出機能 - 設定状況",
            description=f"設定：**{'オン' if row[1] else 'オフ'}**", color=0x00ffff
        ).add_field(
            name="メッセージ送信",
            value=f"チャンネル:{get_channel_ment(row[2])}\n```\n{row[3]}\n```" if row[3] else "未設定"
        ).add_field(
            name="一般ユーザーに付与するロール",
            value=get_role_ment(row[4]) if row[4] else "未設定"
        ).add_field(
            name="ボットに付与するロール",
            value=get_role_ment(row[5]) if row[5] else "未設定"
        ))

    @welcome.command(description="メッセージを送信します")
    @commands.has_guild_permissions(manage_guilds=True)
    async def message(
        self, ctx: GuildContext, channel: discord.TextChannel = commands.CurrentChannel,
        *, content: str = ""
    ):
        if not content:
            if ctx.guild.id not in self.guilds_cache:
                return await ctx.send(f"{emojis.WARNING}この機能は設定されていません。")
                await self.bot.execute_sql(
                    """UPDATE Welcome SET Message = NULL WHERE GuildId = %s;""",
                    (ctx.guild.id,)
                )
            return await ctx.send(f"{emojis.CHECK_MARK}メッセージ送信をしなくなりました。")
        await self.bot.execute_sql(
            """INSERT INTO Welcome VALUES (%s, 1, %s, %s, 0, 0)
                ON DUPLICATE KEY UPDATE Message = VALUES(Message);""",
            (ctx.guild.id, channel.id, content)
        )
        await ctx.send(f"{emojis.CHECK_MARK}登録しました。")

    @welcome.command(description="ロールを付与します。")
    @commands.has_guild_permissions(manage_guilds=True, manage_roles=True)
    async def role(
        self, ctx: GuildContext, mode: Literal["user", "bot", "all"],
        role: discord.Role | None = None
    ):
        mode_dic = {"user": "一般ユーザー", "bot": "Bot", "all": "すべての人"}
        if not role:
            if ctx.guild.id not in self.guilds_cache:
                return await ctx.send(f"{emojis.WARNING}この機能は設定されていません。")
            if mode == "user":
                await self.bot.execute_sql(
                    """UPDATE Welcome SET UserRole = 0 WHERE GuildId = %s;""",
                    (ctx.guild.id,)
                )
            if mode == "bot":
                await self.bot.execute_sql(
                    """UPDATE Welcome SET BotRole = 0 WHERE GuildId = %s;""",
                    (ctx.guild.id,)
                )
            if mode == "all":
                await self.bot.execute_sql(
                    """UPDATE Welcome SET UserRole = 0, BotRole = 0 WHERE GuildId = %s;""",
                    (ctx.guild.id,)
                )
            return await ctx.send(f"{emojis.CHECK_MARK}ロール付与をしなくなりました。")
        await self.bot.execute_sql(
            """INSERT INTO Welcome VALUES (%s, 1, %s, NULL, %s, %s)
                ON DUPLICATE KEY UPDATE UserRole = VALUES(UserRole), BotRole = VALUES(BotRole);""",
            (ctx.guild.id, ctx.channel.id,
             role.id if mode in ["user", "all"] else 0,
             role.id if mode in ["bot", "all"] else 0)
        )
        await ctx.send(f"{emojis.CHECK_MARK}登録しました。")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id not in self.guilds_cache:
            return
        (welcome_data,) = await self.bot.execute_sql(
            "SELECT * FROM Welcome WHERE GuildId = %s LIMIT 1;",
            (member.guild.id,), _return_type="fetchone"
        )
        # メッセージ送信
        if welcome_data[3]:
            channel = self.bot.get_channel(welcome_data[2])
            if isinstance(channel, discord.TextChannel):
                await channel.send(self.welcome_replace(welcome_data[3], member))

        # ロール付与
        if (not member.bot) and welcome_data[4]:
            if (role := member.guild.get_role(welcome_data[4])):
                await member.add_roles(role)
        if member.bot and welcome_data[5]:
            if (role := member.guild.get_role(welcome_data[5])):
                await member.add_roles(role)

    def welcome_replace(self, content: str, member: discord.Member) -> str:
        return (
            content.replace("$member$", str(member)).replace("$member_id$", member.id)
            .replace("$member_name$", member.name).replace("$member_ment$", member.mention)
            .replace("$member_mention$", member.mention).replace("$user$", str(member))
            .replace("$user_id$", member.id).replace("$user_name$", member.name)
            .replace("$user_ment$", member.mention).replace("$user_mention$", member.mention)
            .replace("$guild$", member.guild.name).replace("$guild_name$", member.guild.name)
            .replace("$guild_id$", member.guild.id)
            .replace("$member_count$", len(member.guild.members))
            .replace("$user_count$", str(len(member.guild.members)))
            .replace("$bot_count$", str(len([1 for m in member.guild.members if m.bot])))
            .replace("$non_bot_count$", str(len([1 for m in member.guild.members if not m.bot])))
            .replace("$EMOJI_INFO$", emojis.INFO).replace("$EMOJI_WARNING$", emojis.WARNING)
            .replace("$EMOJI_CHECK_MARK$", emojis.CHECK_MARK)
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Welcome(bot))
