from typing import Literal
from collections.abc import Callable

import asyncio
import aiohttp
import audioop
import copy
import re
import urllib.parse
import urllib.request
from logging import getLogger
from time import time

import discord
import requests
from discord.ext import commands
from niconico.niconico import NicoNico
from youtube_dl import YoutubeDL

from utils import Bot, GuildContext, TimeoutView
from nicovideo_api_client.api.v2.snapshot_search_api_v2 import SnapshotSearchAPIV2
from nicovideo_api_client.constants import FieldType


async def yf_gettitle(id: str, session: aiohttp.ClientSession) -> str:
    searchurl = "https://ysmfilm.wjg.jp/view_raw.php?id=" + id
    async with session.get(searchurl) as ut:
        return (await ut.read()).decode()


async def yf_getduration(id: str, session: aiohttp.ClientSession):
    searchurl = "https://ysmfilm.wjg.jp/duration.php?id=" + id
    async with session.get(searchurl) as ut:
        return (await ut.read()).decode()


niconico = NicoNico()


def fmt_time(time: str | int) -> str:
    if time == '--:--:--':
        return '--:--:--'
    else:
        time = int(time)
        return f"{time // 3600:02d}:{(time % 3600) // 60:02d}:{time % 60:02d}"


def restore(sid: str):
    "VideoIdの文字列のURLへの置き換えを行います。"
    return sid.replace("daily:", "https://www.dailymotion.com/video/"
        ).replace("bili:", "https://www.bilibili.com/video/"
        ).replace("sc:", "https://soundcloud.com/"
        ).replace("nico:", "https://www.nicovideo.jp/watch/"
        ).replace("yf:", "https://ysmfilm.net/view.php?id=")


class Queue:
    duration: int | Literal["--:--:--"]
    sid: str
    source: str
    title: str
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True',
                   "ignoreerrors": True, "cookiefile": "data/youtube.com_cookies.txt"}
    BILIBILI_OPTIONS = {'noplaylist': 'True', "ignoreerrors": True,
                        "cookiefile": "data/youtube.com_cookies.txt"}

    def __init__(self, url: str, session: aiohttp.ClientSession):
        self.url = url
        self.video = None
        self.session = session

    async def setdata(self):
        try:
            if "nicovideo.jp" in self.url or "nico.ms" in self.url:
                if self.video is not None:
                    self.video.close()
                video = niconico.video.get_video(self.url)
                video.connect()
                self.source = video.download_link
                self.title = video.video.title
                self.duration = video.video.duration
                self.sid = "nico:" + video.video.id
                self.video = video
            elif "soundcloud" in self.url:
                if "goo.gl" in self.url:
                    self.url = requests.get(self.url).url
                with YoutubeDL(self.YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise KeyError("info not found")
                self.source = info['url']
                self.title = info['title']
                self.duration = info["duration"]
                self.sid = self.url.replace("https://soundcloud.com/", "sc:")
            elif "ysmfilm" in self.url:
                qs = urllib.parse.urlparse(self.url).query
                qs_d = urllib.parse.parse_qs(qs)
                dar = (await yf_getduration(qs_d['id'][0], self.session)).split(':')
                self.duration = int(dar[0]) * 360 + int(dar[1]) * 60 + int(dar[2])
                self.title = await yf_gettitle(qs_d['id'][0], self.session)
                self.source = "https://ysmfilm.wjg.jp/video/" + qs_d['id'][0] + ".mp4"
                self.sid = "yf:" + qs_d['id'][0]
            elif urllib.parse.urlparse(self.url).path.endswith(('.mp4', 'mp3')):
                self.duration = '--:--:--'
                self.title = self.url
                self.source = self.url
                self.sid = self.url
            elif "bilibili" in self.url:
                with YoutubeDL(self.BILIBILI_OPTIONS) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise KeyError("info not found")
                self.source = info["formats"][0]['url']
                self.title = info['title']
                self.duration = info["duration"]
                self.sid = "bili:" + info["webpage_url"].replace(
                    "https://www.bilibili.com/video/", "", 1)
            elif "dailymotion" in self.url:
                x = copy.copy(self.YDL_OPTIONS)
                x["format"] = "mp4"
                with YoutubeDL(x) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise KeyError("info not found")
                self.source = info['url']
                self.title = info['title']
                self.duration = info["duration"]
                self.sid = "daily:" + info["id"]
        except Exception:
            getLogger(__name__).exception("Music Loading Error.")

    def close(self):
        del self.source
        # ニコニコ用
        if self.video is not None:
            self.video.close()
            self.video = None


class Music(commands.Cog):

    URL_PATTERN = re.compile("https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+")

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self):
        async def sqler(cur):
            await cur.execute("""CREATE TABLE if not exists MusicRanking(
                VideoId VARCHAR(300) PRIMARY KEY NOT NULL,
                Count BIGINT NOT NULL DEFAULT 0
            );""")
            await cur.execute("""CREATE TABLE if not exists MusicList(
                ListId BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                UserId BIGINT NOT NULL,
                VideoId VARCHAR(300) NOT NULL,
                ListName VARCHAR(300) NOT NULL
            );""")
        await self.bot.execute_sql(sqler)

    queues: dict[int, list["Queue"]] = {}
    lop: dict[int, bool] = {}
    lopq: dict[int, list["Queue"]] = {}

    @commands.command()
    @commands.guild_only()
    async def loop(self, ctx: GuildContext):
        if self.lop.get(ctx.guild.id, False):
            self.lop[ctx.guild.id] = False
            self.lopq[ctx.guild.id] = []
            await ctx.send("ループを解除しました")
        else:
            self.lop[ctx.guild.id] = True
            self.lopq[ctx.guild.id] = copy.copy(self.queues[ctx.guild.id])
            await ctx.send("ループを設定しました")

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx: GuildContext, *, url: str):
        if re.match(self.URL_PATTERN, url):
            await self._play(ctx, url)
        else:
            view = TimeoutView([SearchList(ctx, self, url)])
            await view.send(ctx, "検索結果から曲を選んでください。")

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    async def _play(self, ctx: GuildContext, url: str):
        # メインの再生関数
        loop = self.bot.loop
        if not ctx.author.voice:
            return await ctx.send("先にボイスチャンネルに接続してください。")
        channel = ctx.author.voice.channel
        if not channel:
            return await ctx.send("接続するボイスチャンネルを発見できませんでした。")
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if isinstance(voice, discord.VoiceClient) and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        assert isinstance(voice, discord.VoiceClient)

        def nextqueue(_):
            asyncio.run_coroutine_threadsafe(self.asyncnextqueue(
                self.FFMPEG_OPTIONS, voice, ctx, nextqueue), loop)
        self.lop.setdefault(ctx.guild.id, False)
        self.queues.setdefault(ctx.guild.id, [])

        if ("nicovideo.jp" in url or "nico.ms" in url) and "mylist" in url:
            qpl = len(self.queues[ctx.guild.id])
            for mylist in niconico.video.get_mylist(url):
                for item in mylist.items:
                    qp = Queue("https://www.nicovideo.jp/watch/" + item.video.id,
                               self.bot.session)
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
            qp = Queue(url, self.bot.session)
            await qp.setdata()
            if self.lop[ctx.guild.id]:
                self.lopq[ctx.guild.id].append(qp)
            self.queues[ctx.guild.id].append(qp)
        if voice.is_playing() and getattr(voice.source, "music"):
            await ctx.send(f'{qp.title}をキューに追加しました')
        else:
            self.start = time()
            if not voice.is_playing():
                voice.play(AudioMixer(discord.FFmpegPCMAudio(
                    qp.source, **self.FFMPEG_OPTIONS)), after=nextqueue)
            else:
                pcm = discord.FFmpegPCMAudio(qp.source, **self.FFMPEG_OPTIONS)
                setattr(pcm, "nextqueue", nextqueue)
            setattr(voice.source, "music", True)
            ebd = discord.Embed(title=f"{qp.title}を再生します", color=self.bot.Color)
            ebd.add_field(name="Title", value=f"[{qp.title}]({qp.url})")
            ebd.add_field(name="Time", value=fmt_time(0) + "/" + fmt_time(qp.duration))

            button = AplButton(qp, self.bot)
            button._view = TimeoutView([button])
            await button._view.send(ctx, embed=ebd)
            await self.addc(qp)

    async def addc(self, qp: "Queue"):
        "ランキングデータを更新します。"
        await self.bot.execute_sql(
            """INSERT INTO MusicRanking VALUES (%s, 1)
                ON DUPLICATE KEY UPDATE Count = Count + 1""",
            (qp.sid,)
        )

    async def asyncnextqueue(
        self, FFMPEG_OPTIONS, voice: discord.VoiceClient, ctx: GuildContext, nextqueue: Callable
    ):
        if 0 < len(self.queues[ctx.guild.id]):
            try:
                self.queues[ctx.guild.id][0].close()
                self.queues[ctx.guild.id].pop(0)
                qp = self.queues[ctx.guild.id][0]
                await qp.setdata()
                self.start = time()
                if not voice.is_playing():
                    voice.play(AudioMixer(discord.FFmpegPCMAudio(
                        qp.source, **FFMPEG_OPTIONS)), after=nextqueue)
                else:
                    pcm = discord.FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS)
                    setattr(pcm, "nextqueue", nextqueue)
                voice.is_playing()
                await self.addc(qp)
            except IndexError:
                if self.lop[ctx.guild.id]:
                    self.queues[ctx.guild.id] = copy.copy(
                        self.lopq[ctx.guild.id])
                else:
                    return
                qp = self.queues[ctx.guild.id][0]
                await qp.setdata()
                self.start = time()
                if not voice.is_playing():
                    voice.play(AudioMixer(discord.FFmpegPCMAudio(
                        qp.source, **FFMPEG_OPTIONS)), after=nextqueue)
                else:
                    pcm = discord.FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS)
                    setattr(pcm, "nextqueue", nextqueue)
                setattr(voice.source, "music", True)
                await self.addc(qp)

    @commands.command(description="音楽を再生します。")
    @commands.guild_only()
    async def playlist(self, ctx: GuildContext, *, name: str):
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        loop = asyncio.get_event_loop()
        if not ctx.author.voice:
            return await ctx.send("ボイスチャンネルに接続してください！")
        channel = ctx.author.voice.channel
        if not channel:
            return await ctx.send("接続先のチャンネルを見つけることができませんでした。")

        voice = ctx.guild.voice_client
        assert isinstance(voice, discord.VoiceClient)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        def nextqueue(_):
            asyncio.run_coroutine_threadsafe(
                self.asyncnextqueue(FFMPEG_OPTIONS, voice, ctx, nextqueue), loop
            )
        self.lop.setdefault(ctx.guild.id, False)
        self.queues.setdefault(ctx.guild.id, [])

        res = await self.bot.execute_sql(
            "SELECT * FROM MusicList WHERE UserId = %s and ListName = %s",
            (ctx.author.id, name), _return_type="fetchall"
        )
        if not res:
            return await ctx.send("プレイリストが見つかりませんでした。")
        qpl = len(self.queues[ctx.guild.id])
        qp = None
        for row in res:
            qp = Queue(restore(row[1]), self.bot.session)
            await qp.setdata()
            if self.lop[ctx.guild.id]:
                self.lopq[ctx.guild.id].append(qp)
            self.queues[ctx.guild.id].append(qp)
        if not voice.is_playing():
            qp = self.queues[ctx.guild.id][qpl]
        if voice.is_playing() and getattr(voice.source, "music", False):
            return await ctx.send('プレイリストをキューに追加しました')
        self.start = time()

        if not qp:
            return

        if not voice.is_playing():
            voice.play(AudioMixer(discord.FFmpegPCMAudio(
                qp.source, **FFMPEG_OPTIONS)), after=nextqueue)
        else:
            pcm = discord.FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS)
            setattr(pcm, "nextqueue", nextqueue)
        setattr(voice.source, "music", True)
        ebd = discord.Embed(title=qp.title + "を再生します",
                            color=self.bot.Color)
        ebd.add_field(
            name="Title", value=f"[{qp.title}]({qp.url})")
        ebd.add_field(name="Time", value=fmt_time(0) + "/" + fmt_time(qp.duration))
        button = AplButton(qp, self.bot)
        button._view = TimeoutView([button])
        await button._view.send(ctx, embed=ebd)
        await self.addc(qp)

    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: GuildContext):
        voice = ctx.guild.voice_client
        if not voice:
            return await ctx.send("接続していません。")
        assert isinstance(voice, discord.VoiceClient)
        self.stopt = time() - self.start
        if voice.is_playing():
            voice.pause()
            setattr(voice.source, "music", False)
            await ctx.send('一時停止しました')

    @commands.command(description="音楽再生を一時停止します")
    @commands.guild_only()
    async def stop(self, ctx: GuildContext):
        voice = ctx.guild.voice_client
        if not voice:
            return await ctx.send("接続していません。")
        assert isinstance(voice, discord.VoiceClient)

        if voice.is_playing():
            await ctx.send('キューを削除し一時停止しました')
            for qp in self.queues[ctx.guild.id]:
                qp.close()
            self.queues[ctx.guild.id] = list()
            self.lopq[ctx.guild.id] = list()
            setattr(voice.source, "music", False)
            voice.stop()

    @commands.command(description="音楽再生を再開します")
    @commands.guild_only()
    async def resume(self, ctx: GuildContext):
        voice = ctx.guild.voice_client
        if not voice:
            return await ctx.send("接続されていません。")
        assert isinstance(voice, discord.VoiceClient)
        self.start = time() - self.stopt
        if not voice.is_playing():
            voice.resume()
            setattr(voice.source, "music", True)
            await ctx.send('再開しました')

    @commands.command()
    @commands.guild_only()
    async def queue(self, ctx: GuildContext):
        if not self.queues.get(ctx.guild.id):
            return await ctx.send("キューが存在しません。")
        await ctx.send(embed=discord.Embed(
            title="キュー",
            description="\n".join(
                f"[{i.title}]({i.url})" for i in self.queues[ctx.guild.id]
            ), color=self.bot.Color
        ))

    @commands.command()
    async def musicranking(self, ctx: commands.Context):
        res = await self.bot.execute_sql(
            "SELECT * FROM MusicRanking ORDER BY Count desc limit 10",
            _return_type="fetchall"
        )
        i = 1
        list = ""
        for row in res:
            que = Queue(restore(row[1]), self.bot.session)
            await que.setdata()
            list += f"{i}位 [{que.title}]({que.url})\n"
            i += 1
            que.close()
        embed = discord.Embed(
            title="よく聞かれている曲", description=list, color=self.bot.Color)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def disconnect(self, ctx: GuildContext):
        voice = ctx.guild.voice_client
        if not voice:
            return await ctx.send("接続していません。")
        assert isinstance(voice, discord.VoiceClient)

        await voice.disconnect()
        self.queues[ctx.guild.id] = list()
        for qp in self.queues[ctx.guild.id]:
            qp.close()
        self.queues[ctx.guild.id] = list()
        self.lopq[ctx.guild.id] = list()
        await ctx.send('キューを削除し切断しました')

    @commands.command()
    @commands.guild_only()
    async def nowplaying(self, ctx: GuildContext):
        ebd = discord.Embed(title="Now", color=self.bot.Color)
        qp = self.queues[ctx.guild.id][0]
        ebd.add_field(name="Title", value="[" + qp.title + "](" + qp.url + ")")
        ebd.add_field(name="Time", value=fmt_time(
            int(time() - self.start)) + "/" + fmt_time(qp.duration))
        view = TimeoutView([AplButton(qp, self.bot)])
        await view.send(ctx, embed=ebd)

    @commands.command()
    async def editplaylist(self, ctx: commands.Context, name: str):
        res = await self.bot.execute_sql(
            "SELECT * FROM MusicList WHERE UserId = %s and ListName = %s",
            (ctx.author.id, name), _return_type="fetchall"
        )
        if len(res) == 0:
            await ctx.send("このプレイリストには曲が存在しないか、作られていません。")
            return
        i = 1
        list = ""
        for row in res:
            que = Queue(restore(row[1]), self.bot.session)
            await que.setdata()
            list += f"No.{i}[{que.title}]({que.url})\n"
            i = i + 1
            que.close()
        embed = discord.Embed(
            title=name, description=list, color=self.bot.Color)
        await ctx.send(embed=embed)
        try:
            while True:
                d = await self.input(ctx, "削除する曲のNoを数字で入力してください。キャンセルする場合はキャンセルと送ってください")
                if d.content == "キャンセル":
                    await ctx.send("キャンセルしました")
                    break
                await self.bot.execute_sql(
                    "DELETE FROM MusicList WHERE UserId = %s and `lname` = %s and `id` = %s limit 1",
                    (ctx.author.id, name, res[int(d.content) - 1][3])
                )
                await ctx.send("削除しました")
        except SyntaxError:
            await ctx.send("キャンセルしました")

    async def input(self, ctx: commands.Context, q: str):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout=180.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break


class SearchList(discord.ui.Select):
    _view: TimeoutView | None = None

    def __init__(self, ctx: GuildContext, cog: Music, query: str):
        # ニコニコで検索
        args = SnapshotSearchAPIV2().keywords().query(query.split(" ")).field(
            {FieldType.TITLE, FieldType.CONTENT_ID}
        ).sort(FieldType.VIEW_COUNTER).no_filter().limit(10).user_agent(
            "NicoApiClient", "0.5.0"
        ).request().json()["data"]
        self.cog = cog
        self.ctx = ctx
        options = []
        for item in args:
            options.append(discord.SelectOption(
                label=item["title"],
                description=f"https://www.nicovideo.jp/watch/{item['contentId']}",
                value=f"https://www.nicovideo.jp/watch/{item['contentId']}"
            ))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self._view and await self._view.check(interaction):
            return
        await interaction.response.edit_message(content="")
        await self.cog._play(self.ctx, self.values[0])


class AplButton(discord.ui.Button):
    
    _view: TimeoutView | None = None

    def __init__(self, queue: "Queue", bot: Bot):
        self.queue = queue
        self.bot = bot
        super().__init__(label="プレイリストに追加", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        if self._view and self._view.check(interaction):
            return
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        await interaction.response.send_message("追加先のプレイリストの名前を入力してください")
        try:
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await interaction.response.edit_message(
                content='タイムアウトしました.  再度操作をやり直してね'
            )
            return
        else:
            await self.bot.execute_sql(
                "INSERT INTO `musiclist` (`userid`,`vid`,`lname`) VALUES (%s,%s,%s);",
                (interaction.user.id, self.queue.sid, message.content)
            )
            await message.channel.send('追加完了しました')


class AudioMixer(discord.AudioSource):
    def __init__(self, msource):
        super().__init__()
        self.s = []
        self.s.append(msource)
        self.music = False
        self.tts = False

    def read(self):
        data = bytes(3840)
        for pcm in self.s:
            pcmdata = pcm.read()
            if not pcmdata:
                if getattr(pcm, "nextqueue", None) is not None:
                    getattr(pcm, "nextqueue")(pcm.cog)
                pcm.cleanup()
                self.s.remove(pcm)
            else:
                data = audioop.add(data, pcmdata, 2)
        if len(self.s) == 0:
            return bytes()
        else:
            return data


async def setup(bot: Bot):
    await bot.add_cog(Music(bot))
