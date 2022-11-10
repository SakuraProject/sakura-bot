# Sakura bot - mail

from __future__ import annotations

from typing import Any

from orjson import loads
import discord
from discord.ext import commands, tasks
from datetime import datetime
import imaplib
import email
import time
import re
from email.header import decode_header
import asyncio

from utils import Bot, dumps


class OverloadIMAP4:
    user: Any
    lt: Any
    pas: Any
    dch: Any

    def __init__(self, original: imaplib.IMAP4 | imaplib.IMAP4_SSL):
        self.original = original


class PM(discord.ui.Modal):

    def __init__(self, cog: "Mail"):
        super().__init__(title="登録するメールアカウントの情報を入力してください", timeout=None)
        self.cog = cog
        self.mname = discord.ui.TextInput(label="登録するメールアドレスを入力してください")
        self.add_item(self.mname)
        self.s = discord.ui.TextInput(label="IMAPサーバーのurlを入力してください")
        self.add_item(self.s)
        self.port = discord.ui.TextInput(label="IMAPサーバーのportを入力してください")
        self.add_item(self.port)
        self.user = discord.ui.TextInput(label="IMAPのユーザー名を入力してください")
        self.add_item(self.user)
        self.pas = discord.ui.TextInput(label="IMAPのパスワードを入力してください")
        self.add_item(self.pas)

    async def on_submit(self, interaction: discord.Interaction):
        assert interaction.channel and interaction.guild
        await interaction.response.send_message(content="接続を確認中です", ephemeral=True)
        try:
            try:
                m = imaplib.IMAP4(self.s.value, int(self.port.value))
            except Exception:
                m = imaplib.IMAP4_SSL(self.s.value, int(self.port.value))
            m = OverloadIMAP4(m)
            m.original.login(self.user.value, self.pas.value)
            m.user = self.user.value
            m.pas = self.pas.value
            m.dch = interaction.channel
            m.lt = time.time()
            self.cog.nlis.append(m)
            self.cog.chl.setdefault(interaction.channel.id, dict())
            self.cog.chl[interaction.channel.id][self.mname.value] = m
            async with self.cog.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    d = {
                        "s": self.s.value,
                        "port": self.port.value,
                        "user": self.user.value,
                        "pas": self.pas.value
                    }
                    await cur.execute("INSERT INTO `mailnof` (`gid`, `cid`, `mname`, `data`) VALUES (%s,%s,%s,%s);", (interaction.guild.id, interaction.channel.id, self.mname.value, dumps(d)))
            await interaction.response.edit_message(content="登録完了しました")
        except Exception:
            await interaction.response.edit_message(content="接続確認に失敗しました")


class Mail(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.nlis: list[OverloadIMAP4] = []
        self.chl: dict[int, dict[str, OverloadIMAP4]] = {}
        self.noftask.start()

    async def cog_load(self):
        csql = "CREATE TABLE if not exists `mailnof` (`gid` BIGINT NOT NULL, `cid` BIGINT NOT NULL, `mname` VARCHAR(1000) NOT NULL, `data` JSON NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(csql)
                await cur.execute("SELECT * FROM `mailnof`")
                res = await cur.fetchall()
                for row in res:
                    ch = await self.bot.fetch_channel(int(row[1]))
                    if ch is not None:
                        try:
                            d = loads(row[3])
                            try:
                                m = imaplib.IMAP4(d["s"], int(d["port"]))
                            except Exception:
                                m = imaplib.IMAP4_SSL(d["s"], int(d["port"]))
                            m = OverloadIMAP4(m)
                            m.user = d["user"]
                            m.pas = d["pas"]
                            m.original.login(m.user, m.pas)
                            m.dch = ch
                            m.lt = time.time()
                            self.nlis.append(m)
                            self.chl.setdefault(ch.id, dict())
                            self.chl[ch.id][row[2]] = m
                        except Exception:
                            continue

    @tasks.loop(seconds=180)
    async def noftask(self):
        for m in self.nlis:
            try:
                dtmt = None
                m.original.select()
                d = m.original.search(None, datetime.fromtimestamp(
                    m.lt).strftime("(SINCE \"%d-%B-%Y\")"))
                for n in d[1][0].split():
                    h, dt = m.original.fetch(n, '(RFC822)')
                    if dt[0] is None:
                        continue
                    dtm = email.message_from_string(dt[0][1].decode())  # type: ignore
                    # ↑全く何してるかわからん。。。
                    dte = re.sub(" [(]([A-Z]*)[)]", "", dtm["Date"])
                    try:
                        dtmt = datetime.strptime(
                            dte, "%a, %d %b %Y %X %z").timestamp()
                    except Exception:
                        dtmt = datetime.strptime(
                            dte, "%d %b %Y %X %z").timestamp()
                    if m.lt < dtmt:
                        wh = await self.getwebhook(m.dch)
                        subject = decode_header(dtm.get('Subject'))[
                            0][0].decode()
                        fro = dtm["From"]
                        payload = "..."
                        if dtm.is_multipart():
                            for part in dtm.walk():
                                payload = part.get_payload(decode=True)
                                if payload is None:
                                    continue
                                charset = part.get_content_charset()
                                if charset is not None:
                                    payload = payload.decode(charset, "ignore")
                        else:
                            payload = dtm.get_payload(decode=True)
                            charset = dtm.get_content_charset()
                            if charset is not None:
                                payload = payload.decode(charset, "ignore")
                        if len(payload) > 1024:
                            payload = payload[:1024]
                        embed = discord.Embed(
                            title="SakuraBotメール通知", description="新着メールです")
                        embed.add_field(name="送り主", value=fro)
                        embed.add_field(name="タイトル", value=subject)
                        embed.add_field(name="内容", value=payload)
                        await wh.send(embeds=[embed], username="SakuraBotメール通知")
                if dtmt is not None:
                    m.lt = dtmt
            except Exception as e:
                continue

    async def getwebhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name='sakurabot')
        if webhook is None:
            webhook = await channel.create_webhook(name='sakurabot')
        return webhook

    @commands.group(description="メールをdiscordに送信する機能")
    @commands.guild_only()
    async def mail(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @mail.command(description="メール通知を解除します")
    async def remove(self, ctx: commands.Context):
        def check(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        assert ctx.guild
        await ctx.send("DMを確認してください")
        await ctx.author.send("登録したメールアドレスを入力してください")
        try:
            message = await self.bot.wait_for('message', timeout=360.0, check=check)
        except asyncio.TimeoutError:
            await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            mname = message.content
        m = self.chl[ctx.channel.id][mname]
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from `mailnof` where `gid`=%s and `cid`=%s and `mname`=%s", (ctx.guild.id, ctx.channel.id, mname))
                self.nlis.remove(m)
                self.chl[ctx.channel.id].pop(mname)
                await ctx.author.send("解除しました")
                await ctx.send("解除しました")

    @mail.command(description="メール通知を設定します")
    async def set(self, ctx: commands.Context):
        assert ctx.guild

        if ctx.interaction is None:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.author.dm_channel
            await ctx.author.send("メール通知設定を開始します")
            await ctx.send("DMを確認してください")
            await ctx.author.send("登録するメールアドレスを入力してください")
            try:
                message = await self.bot.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                mname = message.content
            await ctx.author.send("IMAPサーバーのurlを入力してください")
            try:
                message = await self.bot.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                s = message.content
            await ctx.author.send("IMAPサーバーのportを入力してください")
            try:
                message = await self.bot.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                port = message.content
            await ctx.author.send("IMAPのユーザー名を入力してください")
            try:
                message = await self.bot.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                user = message.content
            await ctx.author.send("IMAPのパスワードを入力してください")
            try:
                message = await self.bot.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                pas = message.content
            mes = await ctx.author.send("接続を確認中です")
            try:
                try:
                    m = imaplib.IMAP4(s, int(port))
                except Exception:
                    m = imaplib.IMAP4_SSL(s, int(port))
                m.login(user, pas)
                m = OverloadIMAP4(m)
                m.user = user
                m.pas = pas
                m.dch = ctx.channel
                m.lt = time.time()
                self.nlis.append(m)
                self.chl.setdefault(ctx.channel.id, dict())
                # self.chl[ctx.channel.id][row[2]] = m
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        d = {
                            "s": s,
                            "port": port,
                            "user": user,
                            "pas": pas
                        }
                        await cur.execute("INSERT INTO `mailnof` (`gid`, `cid`, `mname`, `data`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, ctx.channel.id, mname, dumps(d)))
                await mes.edit(content="登録完了しました")
            except Exception:
                await mes.edit(content="接続確認に失敗しました")
        else:
            await ctx.interaction.response.send_modal(PM(self))


async def setup(bot: Bot):
    await bot.add_cog(Mail(bot))
