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
            """CREATE TABLE IF NOT EXISTS Welcome2(
                GuildId BIGINT PRIMARY KEY NOT NULL, Onoff BOOLEAN, Channel BIGINT,
                Message TEXT, UserRole BIGINT DEFAULT 0, BotRole BIGINT DEFAULT 0,
                UserMessage TEXT
            );"""
        )
        self.guilds_cache: list[int] = []
        lis = await self.bot.execute_sql(
            "SELECT GuildId FROM Welcome2 WHERE OnOff = 1;", _return_type="fetchall"
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
                return getattr(ch, "mention", f"{emojis.WARNING}存在しないチャンネル")
            return f"{emojis.WARNING}存在しないチャンネル"

        def get_role_ment(role_id: int) -> str:
            if (role := ctx.guild.get_role(role_id)):
                return role.mention
            return f"{emojis.WARNING}存在しないロールが指定されています。"

        row = await self.bot.execute_sql(
            "SELECT * FROM Welcome2 WHERE GuildId = %s LIMIT 1;",
            (ctx.guild.id,), _return_type="fetchone"
        )
        await ctx.send(embed=discord.Embed(
            title="入退出機能 - 設定状況",
            description=f"設定：**{'オン' if row[1] else 'オフ'}**", color=0x00ffff
        ).add_field(
            name="メッセージ送信",
            value=f"チャンネル:{get_channel_ment(row[2])}\n```\n{row[3]}\n```" if row[3] else "コンテンツ未設定"
        ).add_field(
            name="一般ユーザーに付与するロール",
            value=get_role_ment(row[4]) if row[4] else "未設定"
        ).add_field(
            name="ボットに付与するロール",
            value=get_role_ment(row[5]) if row[5] else "未設定"
        ).add_field(
            name="ユーザーへのメッセージ送信",
            value=f"```\n{row[6]}\n```" if row[6] else "未設定"
        ))

    @welcome.command(description="ユーザー入出時にメッセージを送信します。")
    @commands.has_guild_permissions(manage_guild=True)
    async def message(
        self, ctx: GuildContext, channel: discord.TextChannel = commands.CurrentChannel,
        *, content: str = ""
    ):
        if not content:
            if ctx.guild.id not in self.guilds_cache:
                return await ctx.send(f"{emojis.WARNING}この機能は設定されていません。")
            await self.bot.execute_sql(
                "UPDATE Welcome2 SET Message = NULL WHERE GuildId = %s;",
                (ctx.guild.id,)
            )
            await ctx.send(f"{emojis.CHECK_MARK}メッセージ送信をしなくなりました。")
            return await self.check_settings(ctx, ctx.guild.id)
        await self.bot.execute_sql(
            """INSERT INTO Welcome2 VALUES (%s, 1, %s, %s, 0, 0, NULL)
                ON DUPLICATE KEY UPDATE Message = VALUES(Message);""",
            (ctx.guild.id, channel.id, content)
        )
        if ctx.guild.id not in self.guilds_cache:
            self.guilds_cache.append(ctx.guild.id)
        await ctx.send(f"{emojis.CHECK_MARK}登録しました。")
        await self.check_settings(ctx, ctx.guild.id)

    @welcome.command(description="ロールを付与します。")
    @commands.has_guild_permissions(manage_guild=True, manage_roles=True)
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
                    "UPDATE Welcome2 SET UserRole = 0 WHERE GuildId = %s;",
                    (ctx.guild.id,)
                )
            if mode == "bot":
                await self.bot.execute_sql(
                    "UPDATE Welcome2 SET BotRole = 0 WHERE GuildId = %s;",
                    (ctx.guild.id,)
                )
            if mode == "all":
                await self.bot.execute_sql(
                    "UPDATE Welcome2 SET UserRole = 0, BotRole = 0 WHERE GuildId = %s;",
                    (ctx.guild.id,)
                )
            await ctx.send(f"{emojis.CHECK_MARK}ロール付与をしなくなりました。")
            return await self.check_settings(ctx, ctx.guild.id)
        if mode == "user":
            await self.bot.execute_sql(
                """INSERT INTO Welcome2 VALUES (%s, 1, 0, NULL, %s, 0, NULL)
                ON DUPLICATE KEY UPDATE UserRole = VALUES(UserRole);""",
                (ctx.guild.id, role.id)
            )
        if mode == "bot":
            await self.bot.execute_sql(
                """INSERT INTO Welcome2 VALUES (%s, 1, 0, NULL, %s, %s, NULL)
                ON DUPLICATE KEY UPDATE BotRole = VALUES(BotRole);""",
                (ctx.guild.id, role.id)
            )
        if mode == "all":
            await self.bot.execute_sql(
                """INSERT INTO Welcome2 VALUES (%s, 1, 0, NULL, %s, %s, NULL)
                ON DUPLICATE KEY UPDATE UserRole = VALUES(UserRole), BotRole = VALUES(BotRole);""",
                (ctx.guild.id, role.id, role.id)
            )
        if ctx.guild.id not in self.guilds_cache:
            self.guilds_cache.append(ctx.guild.id)
        await ctx.send(f"{emojis.CHECK_MARK}登録しました。")
        await self.check_settings(ctx, ctx.guild.id)

    @welcome.command(description="ユーザーのDMにメッセージを送信します。")
    async def user_message(self, ctx: GuildContext, content: str = ""):
        if not content:
            if ctx.guild.id not in self.guilds_cache:
                return await ctx.send(embed=discord.Embed(
                    title=f"{emojis.WARNING}エラー", description="welcome機能が設定されていません。"
                ))
            await self.bot.execute_sql(
                "UPDATE Welcome2 SET UserMessage = NULL WHERE GuildId = %s;",
                (ctx.guild.id,)
            )
            await ctx.send(f"{emojis.CHECK_MARK}ユーザーのDMにメッセージ送信をしなくなりました。")
            return await self.check_settings(ctx, ctx.guild.id)
        await self.bot.execute_sql(
            """INSERT INTO Welcome2 VALUES (%s, 1, 0, NULL, 0, 0, %s)
            ON DUPLICATE KEY UPDATE UserMessage = VALUES(UserMessage);""",
            (ctx.guild.id, content)
        )
        if ctx.guild.id not in self.guilds_cache:
            self.guilds_cache.append(ctx.guild.id)
        await ctx.send(f"{emojis.CHECK_MARK}登録しました。")
        await self.check_settings(ctx, ctx.guild.id)

    @welcome.command(description="手動で機能のオンオフを切り替えます。")
    async def toggle(self, ctx: GuildContext):
        if ctx.guild.id not in self.guilds_cache:
            sql = await self.bot.execute_sql(
                "SELECT * FROM Welcome2 WHERE GuildId = %s LIMIT 1;",
                (ctx.guild.id,), _return_type="fetchone"
            )
            if not sql:
                return await ctx.send(embed=discord.Embed(
                    title=f"{emojis.WARNING}エラー",
                    description="まだ機能を設定したことがないようです。\n"
                                "welcome関連の機能の設定を初めてすると自動でオンになります。"
                ))
            await self.bot.execute_sql(
                "UPDATE Welcome2 Set Onoff = 1 WHERE GuildId = %s;", (ctx.guild.id,)
            )
            self.guilds_cache.append(ctx.guild.id)
            return await ctx.send(f"{emojis.CHECK_MARK}機能をオンにしました。")
        await self.bot.execute_sql(
            "UPDATE Welcome2 Set Onoff = 0 WHERE GuildId = %s;", (ctx.guild.id,)
        )
        self.guilds_cache.remove(ctx.guild.id)
        return await ctx.send(f"{emojis.CHECK_MARK}機能をオフにしました。")

    async def check_settings(self, ctx: GuildContext, guild_id: int):
        sql = await self.bot.execute_sql(
            "SELECT * FROM Welcome2 WHERE GuildId = %s;",
            (guild_id,), _return_type="fetchone"
        )
        if sql[1] and not (sql[3] or sql[4] or sql[5] or sql[6]):
            await self.bot.execute_sql(
                "UPDATE Welcome2 SET Onoff = 0 WHERE GuildId = %s;",
                (guild_id,)
            )
            self.guilds_cache.remove(guild_id)
            await ctx.send(embed=discord.Embed(
                title=f"{emojis.INFO}自動オフ",
                description="welcome機能の設定が存在しなかったので自動で設定をオフにしました。\n"
                            "次回また何らかの機能を設定すれば自動でオンになります。"
            ))
        if (sql[3] or sql[4] or sql[5] or sql[6]) and not sql[1]:
            await self.bot.execute_sql(
                "UPDATE Welcome2 SET Onoff = 1 WHERE GuildId = %s;",
                (guild_id,)
            )
            self.guilds_cache.append(guild_id)
            await ctx.send(embed=discord.Embed(
                title=f"{emojis.INFO}自動オン",
                description="welcome機能の設定をしたので自動で設定をオンにしました。\n"
                            "`sk!welcome toggle`コマンドを使って手動でオンオフを切り替えることができます。"
            ))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id not in self.guilds_cache:
            return
        welcome_data = await self.bot.execute_sql(
            "SELECT * FROM Welcome2 WHERE GuildId = %s LIMIT 1;",
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

        # ユーザーメッセージ送信
        if welcome_data[6]:
            try:
                await member.send(welcome_data[6])
            except:
                pass

    def welcome_replace(self, content: str, member: discord.Member) -> str:
        return (
            content.replace("$member$", str(member)).replace("$member_id$", str(member.id))
            .replace("$member_name$", member.name).replace("$member_ment$", member.mention)
            .replace("$member_mention$", member.mention).replace("$user$", str(member))
            .replace("$user_id$", str(member.id)).replace("$user_name$", member.name)
            .replace("$user_ment$", member.mention).replace("$user_mention$", member.mention)
            .replace("$guild$", member.guild.name).replace("$guild_name$", member.guild.name)
            .replace("$guild_id$", str(member.guild.id))
            .replace("$member_count$", str(len(member.guild.members)))
            .replace("$user_count$", str(len(member.guild.members)))
            .replace("$bot_count$", str(len([1 for m in member.guild.members if m.bot])))
            .replace("$non_bot_count$", str(len([1 for m in member.guild.members if not m.bot])))
            .replace("$EMOJI_INFO$", emojis.INFO).replace("$EMOJI_WARNING$", emojis.WARNING)
            .replace("$EMOJI_CHECK_MARK$", emojis.CHECK_MARK)
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Welcome(bot))
