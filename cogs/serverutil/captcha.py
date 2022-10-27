from typing import Sequence

import discord
from discord.ext import commands
import random
from hashids import Hashids

from cogs.bot.websocket import Websocket
from utils import Bot, dumps


class Captcha(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE if not exists Captcha2 (
                GuildId BIGINT PRIMARY KEY NOT NULL, ChannelId BIGINT NOT NULL,
                RoleId BIGINT NOT NULL, CaptchaType VARCHAR(1000) NOT NULL
            ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4
            COLLATE = utf8mb4_bin;"""
        )

    @commands.group()
    @commands.guild_only()
    async def captcha(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @captcha.command(description="Web認証用パネル作成コマンドです。")
    async def web(self, ctx: commands.Context, role: discord.Role):
        assert ctx.guild
        await self.bot.execute_sql(
            """INSERT INTO Captcha2 VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE GuildId = VALUES(GuildId),
                ChannelId = VALUES(ChannelId), RoleId = VALUES(RoleId),
                CaptchaType = VALUES(CaptchaType);""",
            (ctx.guild.id, ctx.channel.id, role.id, "web")
        )
        await ctx.send(embed=discord.Embed(
            title="認証パネル", color=self.bot.Color,
            description="このサーバを利用するには認証が必要です。ボタンをおして認証を開始して下さい"
        ), view=MainView([discord.ui.Button(
            label="認証を開始", custom_id="sakurawebcaptcha",
            style=discord.ButtonStyle.green
        )]))

    @captcha.command(description="パスワード認証用パネル作成コマンド")
    async def password(self, ctx: commands.Context, role: discord.Role, password: str):
        assert ctx.guild
        await self.bot.execute_sql(
            """INSERT INTO Captcha2 VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE GuildId = VALUES(GuildId),
                ChannelId = VALUES(ChannelId), RoleId = VALUES(RoleId),
                CaptchaType = VALUES(CaptchaType);""",
            (ctx.guild.id, ctx.channel.id, role.id, f"pass:{password}")
        )
        await ctx.send(embed=discord.Embed(
            title="認証パネル", color=self.bot.Color,
            description="このサーバを利用するには認証が必要です。ボタンをおして認証を開始して下さい"
        ), view=MainView([discord.ui.Button(
            label="認証を開始", custom_id="sakurapasscaptcha",
            style=discord.ButtonStyle.green
        )]))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data:
            return
        if interaction.data.get("custom_id", "") == "sakurawebcaptcha":
            correct_code = random.randint(10000, 99999)
            option = []
            for _ in range(10):
                option.append(discord.SelectOption(
                    label=str(random.randint(10000, 99999))
                ))
            option.append(discord.SelectOption(
                label=str(correct_code), value="correct_code"
            ))
            random.shuffle(option)
            ws = self.bot.cogs["Websocket"]
            assert isinstance(ws, Websocket)

            args = {
                "id": Hashids().encode(interaction.user.id), "vcode": correct_code,
            }
            sen = {"cmd": "captcha", "type": "res", "args": args}
            await ws.sock.send(dumps(sen))
            await interaction.response.send_message(
                content="認証を開始します。下のボタンを押してWebページからCaptchaを完了してください。"
                        "完了後認証用コードが表示されるのでセレクトボタンから同じものを選んでください",
                ephemeral=True, view=MainView([discord.ui.Button(
                    label="Web Captchaページへ",
                    url="https://sakura-bot.net/captcha?reqkey=" + args["id"]
                ), NList(self.bot, option)])
            )
        elif interaction.data.get("custom_id", "") == "sakurapasscaptcha":
            m = PasswordModal(self.bot)
            await interaction.response.send_modal(m)


class MainView(discord.ui.View):
    def __init__(self, args: Sequence[discord.ui.Item]):
        super().__init__(timeout=None)

        for txt in args:
            self.add_item(txt)


class NList(discord.ui.Select):
    def __init__(self, bot: Bot, args: list[discord.SelectOption]):
        self.bot = bot
        super().__init__(placeholder='正しい番号を選択', min_values=1, max_values=1, options=args)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "correct_code":
            assert interaction.guild is not None and isinstance(interaction.user, discord.Member)

            response = await self.bot.execute_sql(
                "SELECT * FROM Captcha2 WHERE GuildId = %s;",
                (interaction.guild.id,), _return_type="fetchone"
            )

            role = interaction.guild.get_role(response[2])
            if not role:
                return await interaction.response.send_message("ロールの取得に失敗しました。")
            await interaction.user.add_roles(role, reason="Sakura Captcha")
            await interaction.response.edit_message(content="認証が完了しました", view=None)
        else:
            await interaction.response.edit_message(content="確認コードが間違っています", view=None)


class PasswordModal(discord.ui.Modal):
    def __init__(self, bot: Bot):
        super().__init__(title="認証を開始します。パスワードを入力してください", timeout=None)
        self.textinput = discord.ui.TextInput(
            label="このサーバーで話すにはパスワード認証が必要です。パスワードを入力してください"
        )
        self.bot = bot
        self.add_item(self.textinput)

    async def on_submit(self, interaction: discord.Interaction):
        assert interaction.guild is not None and isinstance(interaction.user, discord.Member)

        (row,) = await self.bot.execute_sql(
            "SELECT * FROM Captcha2 WHERE GuildId = %s;",
            (interaction.guild.id,), _return_type="fetchone"
        )
        if self.textinput.value == row[3][5:]:
            role = interaction.guild.get_role(row[2])
            if not role:
                return await interaction.response.send_message("ロールの取得に失敗しました。")
            await interaction.user.add_roles(role, reason="Sakura Captcha")
            await interaction.response.send_message("認証が完了しました", ephemeral=True)
        else:
            await interaction.response.send_message("パスワードが違います", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Captcha(bot))
