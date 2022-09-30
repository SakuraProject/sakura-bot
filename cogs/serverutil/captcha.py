from typing import Sequence

import discord
from discord.ext import commands
import random
from hashids import Hashids

from utils import Bot, dumps


class captcha(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        csql = "CREATE TABLE if not exists `captcha` (`gid` BIGINT NOT NULL, `cid` BIGINT NOT NULL, `rid` BIGINT NOT NULL, `type` VARCHAR(1000) NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(csql)

    @commands.group()
    async def captcha(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @captcha.command()
    async def web(self, ctx: commands.Context, role: discord.Role):
        """
        NLang ja Web認証用パネル作成コマンドです
        Web認証用のパネルを送信します
        **使いかた：**
        EVAL self.bot.command_prefix+'captcha web ロール'
        ELang ja
        NLang default Panel command for verifying on web Captcha
        Submit a panel to verifying a web Captcha
        **How to use:**
        EVAL self.bot.command_prefix+'captcha web role'
        ELang default
        """
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `captcha` where `gid`=%s and `cid`=%s", (ctx.guild.id, ctx.channel.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `captcha` (`gid`, `cid`, `rid`, `type`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, ctx.channel.id, role.id, "web"))
                else:
                    await cur.execute("UPDATE `captcha` SET `gid` = %s,`cid` = %s,`rid` = %s, `type` = %s where `gid`=%s and `cid`=%s", (ctx.guild.id, ctx.channel.id, role.id, "web", ctx.guild.id, ctx.channel.id))
                embed = discord.Embed(
                    title="認証パネル", color=self.bot.Color, description="このサーバを利用するには認証が必要です。ボタンをおして認証を開始して下さい")
                bts = list()
                button = discord.ui.Button(
                    label="認証を開始", custom_id="sakurawebcaptcha", style=discord.ButtonStyle.green)
                bts.append(button)
                views = MainView(bts)
                await ctx.send(embeds=[embed], view=views)

    @captcha.command()
    async def password(self, ctx: commands.Context, role: discord.Role, password: str):
        """
        NLang ja パスワード認証用パネル作成コマンドです
        パスワード認証用のパネルを送信します
        **使いかた：**
        EVAL self.bot.command_prefix+'captcha password ロール パスワード'
        ELang ja
        NLang default Panel command for verifying on password
        Submit a panel to verifying a password
        **How to use:**
        EVAL self.bot.command_prefix+'captcha password role password'
        ELang default
        """
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `captcha` where `gid`=%s and `cid`=%s", (ctx.guild.id, ctx.channel.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `captcha` (`gid`, `cid`, `rid`, `type`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, ctx.channel.id, role.id, "pass:" + password))
                else:
                    await cur.execute("UPDATE `captcha` SET `gid` = %s,`cid` = %s,`rid` = %s, `type` = %s where `gid`=%s and `cid`=%s", (ctx.guild.id, ctx.channel.id, role.id, "pass:" + password, ctx.guild.id, ctx.channel.id))
                embed = discord.Embed(
                    title="認証パネル", color=self.bot.Color, description="このサーバを利用するには認証が必要です。ボタンをおして認証を開始して下さい")
                bts = list()
                button = discord.ui.Button(
                    label="認証を開始", custom_id="sakurapasscaptcha", style=discord.ButtonStyle.green)
                bts.append(button)
                views = MainView(bts)
                await ctx.send(embeds=[embed], view=views)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data.get("custom_id", "") == "sakurawebcaptcha":
            vcode = random.randint(10000, 99999)
            option = []
            for r in range(10):
                option.append(discord.SelectOption(
                    label=str(random.randint(10000, 99999))))
            option.append(discord.SelectOption(
                label=str(vcode), value="vcode"))
            random.shuffle(option)
            ws = self.bot.cogs["websocket"]
            sen = dict()
            sen["cmd"] = "captcha"
            args = dict()
            hashids = Hashids()
            args["id"] = hashids.encode(interaction.user.id)
            args["vcode"] = vcode
            sen["args"] = args
            sen["type"] = "res"
            await ws.sock.send(dumps(sen))
            bts = list()
            button = discord.ui.Button(
                label="Web Captchaページへ", url="https://sakura-bot.net/captcha?reqkey=" + args["id"])
            bts.append(button)
            lis = NList(self.bot, option)
            bts.append(lis)
            await interaction.response.send_message(content="認証を開始します。下のボタンを押してWebページからCaptchaを完了してください。完了後認証用コードが表示されるのでセレクトボタンから同じものを選んでください", ephemeral=True, view=MainView(bts))
        if interaction.data.get("custom_id", "") == "sakurapasscaptcha":
            m = PM(self.bot)
            await interaction.response.send_modal(m)


class MainView(discord.ui.View):
    def __init__(self, args: Sequence[discord.ui.Item]):
        super().__init__(timeout=None)

        for txt in args:
            self.add_item(txt)


class NList(discord.ui.Select):
    def __init__(self, bot: Bot, args: list[discord.SelectOption]):
        self.bot = bot
        super().__init__(placeholder='', min_values=1, max_values=1, options=args)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "vcode":
            async with self.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM `captcha` where `gid`=%s and `cid`=%s", (interaction.guild.id, interaction.channel.id))
                    res = await cur.fetchall()
                    await conn.commit()
                    role = interaction.guild.get_role(res[0][2])
                    await interaction.user.add_roles(role, reason="Sakura Captcha")
                    await interaction.response.edit_message(content="認証が完了しました", view=discord.ui.View())
        else:
            await interaction.response.edit_message(content="確認コードが間違っています", view=discord.ui.View())


class PassInput(discord.ui.TextInput):
    def __init__(self):
        super().__init__(label="このサーバーで話すにはパスワード認証が必要です。パスワードを入力してください")


class PM(discord.ui.Modal):
    def __init__(self, bot: Bot):
        super().__init__(title="認証を開始します。パスワードを入力してください", timeout=None)
        self.iv = PassInput()
        self.bot = bot
        self.add_item(self.iv)

    async def on_submit(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `captcha` where `gid`=%s and `cid`=%s", (interaction.guild.id, interaction.channel.id))
                res = await cur.fetchall()
                await conn.commit()
                if "pass:" + self.iv.value == res[0][3]:
                    role = interaction.guild.get_role(res[0][2])
                    await interaction.user.add_roles(role, reason="Sakura Captcha")
                    await interaction.response.send_message(content="認証が完了しました", view=discord.ui.View(), ephemeral=True)
                else:
                    await interaction.response.send_message(content="パスワードが違います", view=discord.ui.View(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(captcha(bot))
