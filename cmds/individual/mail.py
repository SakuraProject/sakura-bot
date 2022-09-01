from ujson import loads, dumps
import discord
from discord.ext import commands, tasks
from datetime import datetime
import imaplib
import email
import time
import re
from email.header import decode_header

class PM(discord.ui.Modal):
    def __init__(self,cog):
        super().__init__(title="登録するメールアカウントの情報を入力してください",timeout=None)
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
        mes = await interaction.response.send_message(content="接続を確認中です",view=discord.ui.View(),ephemeral=True)
        try:
            try:
                m = imaplib.IMAP4(self.s.value,int(self.port.value))
            except:
                m = imaplib.IMAP4_SSL(self.s.value,int(self.port.value))
            m.login(self.user.value,self.pas.value)
            m.user = self.user.value
            m,pas = self.pas.value
            m.dch = interaction.channel
            m.lt = time.time()
            cog.nlis.append(m)
            cog.chl.setdefault(interaction.channel.id,dict())
            cog.chl[interaction.channel.id][self.mname.value] = m
            async with cog.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    d = dict()
                    d["s"] = self.s.value
                    d["port"] = self.port.value
                    d["user"] = self.user.value
                    d["pas"] = self.pas.value
                    await cur.execute("INSERT INTO `mailnof` (`gid`, `cid`, `mname`, `data`) VALUES (%s,%s,%s,%s);",(interaction.channel.guild.id,interaction.channel.id,self.mname.value,dumps(d)))
            await mes.edit(content="登録完了しました")
        except:
            await mes.edit(content="接続確認に失敗しました")

class mail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nlis = list()
        self.chl = dict()
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
                                m = imaplib.IMAP4(d["s"],int(d["port"]))
                            except:
                                m = imaplib.IMAP4_SSL(d["s"],int(d["port"]))
                            m.user = d["user"]
                            m.pas = d["pas"]
                            m.login(m.user,m.pas)
                            m.dch = ch
                            m.lt = time.time()
                            self.nlis.append(m)
                            self.chl.setdefault(ch.id,dict())
                            self.chl[ch.id][row[2]] = m
                        except:
                            continue

    @tasks.loop(seconds=180)
    async def noftask(self):
        for m in self.nlis:
            try:
                dtmt = None
                m.select()
                d = m.search(None,datetime.fromtimestamp(m.lt).strftime("(SINCE \"%d-%B-%Y\")"))
                for n in d[1][0].split():
                    h, dt = m.fetch(n, '(RFC822)')
                    dtm = email.message_from_string(dt[0][1].decode())
                    dte = re.sub(" [(]([A-Z]*)[)]","",dtm["Date"])
                    try:
                        dtmt = datetime.strptime(dte,"%a, %d %b %Y %X %z").timestamp()
                    except:
                        dtmt = datetime.strptime(dte,"%d %b %Y %X %z").timestamp()
                    if m.lt < dtmt:
                        wh = await self.getwebhook(m.dch)
                        subject = decode_header(dtm.get('Subject'))[0][0].decode()
                        fro = dtm["From"]
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
                        embed = discord.Embed(title="SakuraBotメール通知",description="新着メールです")
                        embed.add_field(name="送り主", value=fro)
                        embed.add_field(name="タイトル", value=subject)
                        embed.add_field(name="内容", value=payload)
                        await wh.send(embeds=[embed], username="SakuraBotメール通知")
                if dtmt is not None:
                    m.lt = dtmt
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(dte)
                continue
    async def getwebhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name='sakurabot')
        if webhook is None:
            webhook = await channel.create_webhook(name='sakurabot')
        return webhook

    @commands.group()
    async def mail(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")
    @mail.command()
    async def remove(self, ctx):
        """
        NLang ja mail通知を解除するコマンドです
        新着メールをdiscordに送信する機能を解除します
        **使いかた：**
        EVAL self.bot.command_prefix+'mail remove'
        ELang ja
        NLang default This is a command to remove mail notifications.
        remove the ability to send recent mail to discord
        **How to use:**
        EVAL self.bot.command_prefix+'mail remove'
        ELang default
        """
        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        await ctx.send("DMを確認してください")
        await ctx.author.send("登録したメールアドレスを入力してください")
        try:
            message = await client.wait_for('message', timeout=360.0, check=check)
        except asyncio.TimeoutError:
            await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            mname = message.content
        m = self.chl[ctx.channel.id][mname]
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from `mailnof` where `gid`=%s and `cid`=%s and `mname`=%s",(ctx.guild.id,ctx.channel.id,mname))
                self.nlis.remove(m)
                self.chl[ctx.channel.id].pop(mname)
                await ctx.author.send("解除しました")
                await ctx.send("解除しました")
    @mail.command()
    async def set(self, ctx):
        """
        NLang ja mail通知を設定するコマンドです
        新着メールをdiscordに送信する機能を設定します
        **使いかた：**
        EVAL self.bot.command_prefix+'mail set'
        ELang ja
        NLang default This is a command to set mail notifications.
        Set the ability to send recent mail to discord
        **How to use:**
        EVAL self.bot.command_prefix+'mail set'
        ELang default
        """
        if ctx.interaction is None:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.author.dm_channel
            await ctx.author.send("メール通知設定を開始します")
            await ctx.send("DMを確認してください")
            await ctx.author.send("登録するメールアドレスを入力してください")
            try:
                message = await client.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                mname = message.content
            await ctx.author.send("IMAPサーバーのurlを入力してください")
            try:
                message = await client.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                s = message.content
            await ctx.author.send("IMAPサーバーのportを入力してください")
            try:
                message = await client.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                port = message.content
            await ctx.author.send("IMAPのユーザー名を入力してください")
            try:
                message = await client.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                user = message.content
            await ctx.author.send("IMAPのパスワードを入力してください")
            try:
                message = await client.wait_for('message', timeout=360.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                pas = message.content
            mes = await ctx.author.send("接続を確認中です")
            try:
                try:
                    m = imaplib.IMAP4(s,int(port))
                except:
                    m = imaplib.IMAP4_SSL(s,int(port))
                m.login(user,pas)
                m.user = user
                m.pas = pas
                m.dch = ctx.channel
                m.lt = time.time()
                self.nlis.append(m)
                self.chl.setdefault(ctx.channel.id,dict())
                self.chl[ctx.channel.id][row[2]] = m
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        d = dict()
                        d["s"] = s
                        d["port"] = port
                        d["user"] = user
                        d["pas"] = pas
                        await cur.execute("INSERT INTO `mailnof` (`gid`, `cid`, `mname`, `data`) VALUES (%s,%s,%s,%s);",(ctx.guild.id,ctx.channel.id,mname,dumps(d)))
                await mes.edit(content="登録完了しました")
            except:
                await mes.edit(content="接続確認に失敗しました")
        else:
             ctx.interaction.response.send_modal(PM(self))
async def setup(bot):
    global client
    client = bot
    await bot.add_cog(mail(bot))