from niconico import NicoNico
import requests
import urllib.parse
import urllib.request
from youtube_dl import YoutubeDL
import discord
from discord.ext import commands
from discord.utils import get
import re
import asyncio
from discord import FFmpegPCMAudio
import copy
from time import time

def yf_gettitle(id):
    searchurl = "https://ysmfilm.wjg.jp/view_raw.php?id=" + id
    with urllib.request.urlopen(searchurl) as ut:
        tit = ut.read().decode()
    return tit


def yf_getduration(id):
    searchurl = "https://ysmfilm.wjg.jp/duration.php?id=" + id
    with urllib.request.urlopen(searchurl) as ut:
        tit = ut.read().decode()
    return tit

niconico = NicoNico()

def fmt_time(time):
    if time== '--:--:--':
        return '--:--:--'
    else:
        return str(time // 3600) + ":" + str((time - (time // 3600)) // 60) + ":" + str(time % 60)

def restore(sid):
    return sid.replace("sc:","https://soundcloud.com/").replace("yt:","https://youtube.com/watch?v=").replace("nico:","https://www.nicovideo.jp/watch/").replace("yf:","https://ysmfilm.net/view.php?id=")
class Queue():
    def __init__(self,url):
        self.url = url
    async def setdata(self):
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True',"ignoreerrors": True,"cookiefile": "data/youtube.com_cookies.txt"}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        try:
            if "nicovideo.jp" in self.url or "nico.ms" in self.url:
                video = niconico.video.get_video(self.url)
                video.connect()
                self.source = video.download_link
                self.title = video.video.title
                self.duration = video.video.duration
                self.sid = "nico:" + video.video.id
                video.close()
            elif "soundcloud" in self.url:
                if "goo.gl" in self.url:
                    self.url = requests.get(self.url).url
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                self.source = info['url']
                self.title = info['title']
                self.duration = info["duration"]
                self.sid = self.url.replace("https://soundcloud.com/","sc:")
            elif "ysmfilm" in self.url:
                qs = urllib.parse.urlparse(self.url).query
                qs_d = urllib.parse.parse_qs(qs)
                dar = yf_getduration(qs_d['id'][0]).split(':')
                self.duration = int(dar[0]) * 360 + int(dar[1]) * 60 + int(dar[2])
                self.title = yf_gettitle(qs_d['id'][0])
                self.source = "https://ysmfilm.wjg.jp/video/" + qs_d['id'][0] + ".mp4"
                self.sid = "yf:" + qs_d['id'][0]
            elif urllib.parse.urlparse(self.url).path.endswith('.mp4') or urllib.parse.urlparse(self.url).path.endswith('.mp3'):
                self.duration = '--:--:--'
                self.title = self.url
                self.source = self.url
                self.sid = self.url
            elif "youtu" in self.url:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                self.source = info['url']
                self.title = info['title']
                self.duration = info["duration"]
                self.sid = "yt:" + info["id"]
        except Exception as e:
            print(str(e))
            print("Music Load Error")


class music(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""
    async def cog_load(self):
        csql = "CREATE TABLE if not exists `musicranking` ( `count` BIGINT NOT NULL DEFAULT 0, `vid` VARCHAR(300) NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        csql1 = "CREATE TABLE if not exists `gombot`.`musiclist` ( `userid` BIGINT NOT NULL, `vid` VARCHAR(300) NOT NULL, `lname` VARCHAR(300) NOT NULL, `id` BIGINT NOT NULL AUTO_INCREMENT primary key) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(csql)
                await cur.execute(csql1)

    queues = dict()
    lop=dict()
    lopq=dict()
    @commands.command()
    async def loop(self,ctx):
         try:
             if self.lop[ctx.guild.id]:
                 self.lop[ctx.guild.id]=False
                 self.lopq[ctx.guild.id]=list()
                 await ctx.send("ループを解除しました")
             else:
                 self.lop[ctx.guild.id]=True
                 self.lopq[ctx.guild.id]=copy.copy(self.queues[ctx.guild.id])
                 await ctx.send("ループを設定しました")
         except KeyError:
             self.lop[ctx.guild.id]=True
             self.lopq[ctx.guild.id]=copy.copy(self.queues[ctx.guild.id])
             await ctx.send("ループを設定しました")
    @commands.command()
    async def play(self,ctx,url):
        pattern="https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        if not re.match(pattern,url):
            view=discord.ui.View()
            view.add_item(SearchList(ctx,self,url))
            await ctx.send(content="検索結果から曲を選んでください",view=view)
            return
        await self.pl(ctx,url)
    async def pl(self,ctx,url):
        YDL_OPTIONS = {'format': 'bestaudio',"ignoreerrors": True,"cookiefile": "data/youtube.com_cookies.txt"}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        loop =asyncio.get_event_loop()
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        def nextqueue(er):
            if 0<len(self.queues[ctx.guild.id]):
                if not voice.is_playing():
                    try:
                        self.queues[ctx.guild.id].pop(0)
                        qp = self.queues[ctx.guild.id][0]
                        asyncio.run_coroutine_threadsafe(qp.setdata(),loop)
                        self.start = time()
                        voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
                        voice.is_playing()
                        asyncio.run_coroutine_threadsafe(self.addc(qp),loop)
                    except IndexError:
                        if self.lop[ctx.guild.id]:
                            self.queues[ctx.guild.id]=copy.copy(self.lopq[ctx.guild.id])
                        else:
                            return
                        qp = self.queues[ctx.guild.id][0]
                        asyncio.run_coroutine_threadsafe(qp.setdata(),loop)
                        self.start = time()
                        voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
                        voice.is_playing()
                        asyncio.run_coroutine_threadsafe(self.addc(qp),loop)
        try:
            str(self.lop[ctx.guild.id])
        except KeyError:
            self.lop[ctx.guild.id]=False
        try:
            len(self.queues[ctx.guild.id])
        except KeyError:
            self.queues[ctx.guild.id] = list()
        if "youtu" in url:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            if info.get("entries"):
                qpl = len(self.queues[ctx.guild.id])
                for ent in info['entries']:
                    qp = Queue("https://youtube.com/watch?v=" + ent["id"])
                    qp.title = ent["title"]
                    qp.source = ent['url']
                    qp.duration = ent["duration"]
                    qp.sid = "yt:" + ent["id"]
                    if self.lop[ctx.guild.id]:
                        self.lopq[ctx.guild.id].append(qp)
                    self.queues[ctx.guild.id].append(qp)
                if not voice.is_playing():
                    qp = self.queues[ctx.guild.id][qpl]
                else:
                    await ctx.send('プレイリストをキューに追加しました')
                    return
            else:
                qp = Queue(url)
                await qp.setdata()
                if self.lop[ctx.guild.id]:
                    self.lopq[ctx.guild.id].append(qp)
                self.queues[ctx.guild.id].append(qp)
        elif ("nicovideo.jp" in url or "nico.ms" in url) and "mylist" in url:
            qpl = len(self.queues[ctx.guild.id])
            for mylist in niconico.video.get_mylist(url):
                for item in mylist.items:
                    qp = Queue("https://www.nicovideo.jp/watch/" + item.video.id)
                    await qp.setdata()
                    if self.lop[ctx.guild.id]:
                        self.lopq[ctx.guild.id].append(qp)
                    self.queues[ctx.guild.id].append(qp)
            if not voice.is_playing():
                qp = self.queues[ctx.guild.id][qpl]
            else:
                await ctx.send('プレイリストをキューに追加しました')
                return
        else:
            qp = Queue(url)
            await qp.setdata()
            if self.lop[ctx.guild.id]:
                self.lopq[ctx.guild.id].append(qp)
            self.queues[ctx.guild.id].append(qp)
        if not voice.is_playing():
            self.start = time()
            voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
            voice.is_playing()
            ebd = discord.Embed(title=qp.title + "を再生します",color=self.bot.Color)
            ebd.add_field(name="Title", value="[" + qp.title + "](" + qp.url + ")")
            ebd.add_field(name="Time", value=fmt_time(0) + "/" + fmt_time(qp.duration))
            view=discord.ui.View()
            view.add_item(AplButton(qp,self.bot))
            await ctx.send(embeds=[ebd],view=view)
            await self.addc(qp)
        else:
            await ctx.send(qp.title+'をキューに追加しました')

    async def addc(self, qp):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musicranking` where `vid` = %s",(qp.sid,))
                res = await cur.fetchall()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `musicranking` (`count`, `vid`) VALUES (%s,%s);",(1,qp.sid))
                else:
                    ct = int(res[0][0]) + 1
                    await cur.execute("UPDATE `musicranking` SET `count` = %s,`vid` = %s where `vid` = %s;",(ct,qp.sid,qp.sid))

    @commands.command()
    async def playlist(self,ctx,name):
        YDL_OPTIONS = {'format': 'bestaudio',"ignoreerrors": True,"cookiefile": "data/youtube.com_cookies.txt"}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        loop =asyncio.get_event_loop()
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        def nextqueue(er):
            if 0<len(self.queues[ctx.guild.id]):
                if not voice.is_playing():
                    try:
                        self.queues[ctx.guild.id].pop(0)
                        qp = self.queues[ctx.guild.id][0]
                        asyncio.run_coroutine_threadsafe(qp.setdata(),loop)
                        self.start = time()
                        voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
                        voice.is_playing()
                        asyncio.run_coroutine_threadsafe(self.addc(qp),loop)
                    except IndexError:
                        if self.lop[ctx.guild.id]:
                            self.queues[ctx.guild.id]=copy.copy(self.lopq[ctx.guild.id])
                        else:
                            return
                        qp = self.queues[ctx.guild.id][0]
                        asyncio.run_coroutine_threadsafe(qp.setdata(),loop)
                        self.start = time()
                        voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
                        voice.is_playing()
                        asyncio.run_coroutine_threadsafe(self.addc(qp),loop)
        try:
            str(self.lop[ctx.guild.id])
        except KeyError:
            self.lop[ctx.guild.id]=False
        try:
            len(self.queues[ctx.guild.id])
        except KeyError:
            self.queues[ctx.guild.id] = list()
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musiclist` where `userid` = %s and `lname` = %s",(ctx.author.id,name))
                res = await cur.fetchall()
                for row in self.queues[ctx.guild.id]:
                    qp = Queue(restore(row[1]))
                    await qp.setdata()
                    if self.lop[ctx.guild.id]:
                        self.lopq[ctx.guild.id].append(qp)
                    self.queues[ctx.guild.id].append(qp)
                if not voice.is_playing():
                    qp = self.queues[ctx.guild.id][qpl]
        if not voice.is_playing():
            self.start = time()
            voice.play(FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS),after=nextqueue)
            voice.is_playing()
            ebd = discord.Embed(title=qp.title + "を再生します",color=self.bot.Color)
            ebd.add_field(name="Title", value="[" + qp.title + "](" + qp.url + ")")
            ebd.add_field(name="Time", value=fmt_time(0) + "/" + fmt_time(qp.duration))
            view=discord.ui.View()
            view.add_item(AplButton(qp,self.bot))
            await ctx.send(embeds=[ebd],view=view)
            await self.addc(qp)
        else:
            await ctx.send('プレイリストをキューに追加しました')

    @commands.command()
    async def pause(self,ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        self.stopt = time() - self.start
        if voice.is_playing():
            voice.pause()
            await ctx.send('一時停止しました')

    @commands.command()
    async def stop(self,ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if voice.is_playing():
            voice.stop()
            await ctx.send('キューを削除し一時停止しました')
            self.queues[ctx.guild.id]=list()

    @commands.command()
    async def resume(self,ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        self.start = time() - self.stopt
        if not voice.is_playing():
            voice.resume()
            await ctx.send('再開しました')
    @commands.command()
    async def queue(self,ctx):
        list=""
        for que in self.queues[ctx.guild.id]:
            list = list + "[" + que.title + "](" + que.url + ")\n"
        embed=discord.Embed(title="Queue",description=list,color=self.bot.Color)
        await ctx.send(embeds=[embed])

    @commands.command()
    async def musicranking(self,ctx):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musicranking` ORDER BY `count` desc limit 10")
                res = await cur.fetchall()
                i = 1
                list=""
                for row in res:
                    que = Queue(restore(row[1]))
                    await que.setdata()
                    list = list + str(i) + "位 [" + que.title + "](" + que.url + ")\n"
                    i = i + 1
                embed=discord.Embed(title="よく聞かれている曲",description=list,color=self.bot.Color)
                await ctx.send(embeds=[embed])

    @commands.command()
    async def disconnect(self,ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        await voice.disconnect()
        self.queues[ctx.guild.id]=list()

    @commands.command()
    async def nowplaying(self,ctx):
        ebd = discord.Embed(title="Now",color=self.bot.Color)
        qp = self.queues[ctx.guild.id][0]
        ebd.add_field(name="Title", value="[" + qp.title + "](" + qp.url + ")")
        ebd.add_field(name="Time", value=fmt_time(int(time()-self.start)) + "/" + fmt_time(qp.duration))
        view=discord.ui.View()
        view.add_item(AplButton(qp,self.bot))
        await ctx.send(embeds=[ebd],view=view)

    @commands.command()
    async def editplaylist(self,ctx,name):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musiclist` where `userid` = %s and `lname` = %s",(ctx.author.id,name))
                res = await cur.fetchall()
                if len(res) == 0:
                    await ctx.send("このプレイリストには曲が存在しないか、作られていません")
                    return
                i = 1
                list=""
                for row in res:
                    que = Queue(restore(row[1]))
                    await que.setdata()
                    list = list + "No." + str(i) + "[" + que.title + "](" + que.url + ")\n"
                    i = i + 1
                embed=discord.Embed(title=name,description=list,color=self.bot.Color)
                await ctx.send(embeds=[embed])
                try:
                    while True:
                        d = await self.input(ctx,"削除する曲のNoを数字で入力してください。キャンセルする場合はキャンセルと送ってください")
                        if d.content == "キャンセル":
                            await ctx.send("キャンセルしました")
                            break
                        await cur.execute("delete FROM `musiclist` where `userid` = %s and `lname` = %s and `id` = %s limit 1",(ctx.author.id,name,res[int(d.content)-1][3]))
                        await ctx.send("削除しました")
                except SyntaxError:
                    await ctx.send("キャンセルしました")
    async def input(self,ctx,q):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout= 180.0, check= check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout= 180.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break
class SearchList(discord.ui.Select):
    def __init__(self, ctx, cog, query):
        YDL_OPTIONS = {'format': 'bestaudio',"ignoreerrors": True,"cookiefile": "data/youtube.com_cookies.txt"}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info("ytsearch10:" + query, download=False)
        args = info['entries']
        self.sq = args
        self.cog = cog
        self.ctx = ctx
        options = []
        for item in args:
            options.append(discord.SelectOption(label=item["title"], description="https://youtube.com/watch?v=" + item["id"],value="https://youtube.com/watch?v=" + item["id"]))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="選択されました")
        await self.cog.pl(self.ctx,self.values[0])


class AplButton(discord.ui.Button):
    def __init__(self, it,bot):
        self.it = it
        self.bot = bot
        super().__init__(label="プレイリストに追加", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        await interaction.response.send_message("追加先のプレイリストの名前を入力してください")
        try:
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await interaction.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            async with self.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO `musiclist` (`userid`,`vid`,`lname`) VALUES (%s,%s,%s);",(interaction.user.id,self.it.sid,message.content))
                    await interaction.channel.send('追加完了しました')

async def setup(bot):
    await bot.add_cog(music(bot))