import inspect
import asyncio
import importlib
from time import time

import discord
from hashids import Hashids
from ujson import loads, dumps
from discord.ext import commands
from discord import FFmpegPCMAudio

from utils import Bot, GuildContext
from cogs.entertainment import music
# 既存の機能をプラグイン対応可にします
oldrestore = music.restore


def restore(sid):
    res = sid
    ctx = inspect.stack()[1].frame.f_locals["ctx"]
    plugin = bot.cogs["Plugin"]
    enable = plugin.get_enable_pulgin(ctx.author, ctx.guild)
    for plugins in enable:
        try:
            if res == sid:
                res = plugins["Music"].restore(sid)
            else:
                return res
        except Exception:
            continue
    res = oldrestore(sid)
    if res == sid and not sid.startswith("http"):
        return "https://sakura-bot.net"
    else:
        return res


def is_enable(func):
    """プラグインが有効化されているか確認するデコレーターです"""
    async def _is_enable(ctx: commands.Context):
        id = str(func.__module__).split(".")[2].split("_")[0]
        plugin = bot.cogs["Plugin"]
        enable = plugin.get_enable_pulgin(ctx.author, ctx.guild)
        if plugin.plugins[id] not in enable:
            raise commands.CommandNotFound()
        return True

    if isinstance(func, commands.Command):
        func.checks.append(_is_enable)
        if not hasattr(func, '__commands_checks__'):
            setattr(func, "__commands_checks__", [_is_enable])
    return func


class PluginQueue(music.Queue):

    async def setdata(self):
        ctx = inspect.stack()[1].frame.f_locals["ctx"]
        plugin = bot.cogs["Plugin"]
        enable = plugin.get_enable_pulgin(ctx.author, ctx.guild)
        for plugins in enable:
            try:
                await plugins["Music"].setdata(self)
            except Exception:
                continue
        if not hasattr(self, "source"):
            await super().setdata()


class PluginSearchList(music.SearchList):
    def __init__(self, ctx: commands.Context, cog: music.Music, query: str):
        self.cog = cog
        self.ctx = ctx
        items = []
        options = []
        plugin = bot.cogs["Plugin"]
        enable = plugin.get_enable_pulgin(ctx.author, ctx.guild)
        for plugins in enable:
            try:
                item = plugins["Music"].search(query)
                if item is not None and len(item) > 0:
                    items.extend(item)
                if len(items) > 10:
                    break
            except Exception:
                continue
        for item in items:
            options.append(discord.SelectOption(
                label=item["title"], description=item["url"], value=item["url"]))
        if len(options) == 0:
            super().__init__(ctx, cog, query)
        else:
            super(music.SearchList, self) \
                .__init__(placeholder='', min_values=1, max_values=1, options=options)


class Music(music.Music):

    async def is_playlist(self, ctx: commands.Context, url: str):
        res = list()
        plugin = bot.cogs["Plugin"]
        enable = plugin.get_enable_pulgin(ctx.author, ctx.guild)
        for plugins in enable:
            try:
                urls = await plugins["Music"].is_playlist(url)
                if len(urls) > 0:
                    return urls
            except Exception:
                continue
        return res

    async def pl(self, ctx: GuildContext, url: str):
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        self.ifloop = self.lop
        loop = bot.loop
        if not ctx.author.voice:
            return await ctx.send("ボイスチャンネルに接続していません。")
        channel = ctx.author.voice.channel
        if not channel:
            return await ctx.send("接続先のチャンネルが見つかりませんでした。")
        voice = ctx.guild.voice_client
        if isinstance(voice, discord.VoiceClient) and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        def nextqueue(self):
            asyncio.run_coroutine_threadsafe(self.asyncnextqueue(
                FFMPEG_OPTIONS, voice, ctx, nextqueue), loop)
        self.ifloop.setdefault(ctx.guild.id, False)
        self.queues.setdefault(ctx.guild.id, [])
        urls = await self.is_playlist(ctx, url)
        if len(urls) > 0:
            qpl = len(self.queues[ctx.guild.id])
            for u in urls:
                qp = music.Queue(u)
                if self.ifloop[ctx.guild.id]:
                    self.lopq[ctx.guild.id].append(qp)
                self.queues[ctx.guild.id].append(qp)
            if not (voice.is_playing() and getattr(voice.source, "music", False)):
                qp = self.queues[ctx.guild.id][qpl]
                self.start = time()
                if not voice.is_playing():
                    voice.play(music.AudioMixer(FFmpegPCMAudio(
                        qp.source, **FFMPEG_OPTIONS)), after=nextqueue)
                else:
                    pcm = FFmpegPCMAudio(qp.source, **FFMPEG_OPTIONS)
                    setattr(pcm, "nextqueue", nextqueue)
                    setattr(pcm, "cog", self)
                    getattr(voice.source, "s", []).append(pcm)
                setattr(voice.source, "music", True)
                ebd = discord.Embed(title=qp.title + "を再生します",
                                    color=self.bot.Color)
                ebd.add_field(
                    name="Title", value="[" + qp.title + "](" + qp.url + ")")
                ebd.add_field(name="Time", value=music.fmt_time(
                    0) + "/" + music.fmt_time(qp.duration))
                view = discord.ui.View()
                view.add_item(music.AplButton(qp, self.bot))
                await ctx.send(embeds=[ebd], view=view)
                await self.addc(qp)
            else:
                await ctx.send('プレイリストをキューに追加しました')
                return
        else:
            await super().pl(ctx, url)

    @commands.command()
    async def editplaylist(self, ctx: commands.Context, name: str):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musiclist` where `userid` = %s and `lname` = %s", (ctx.author.id, name))
                res = await cur.fetchall()
                if len(res) == 0:
                    return await ctx.send("このプレイリストには曲が存在しないか、作られていません")
                i = 1
                list = ""
                for row in res:
                    que = PluginQueue(restore(row[1]))
                    if que.url == "https://sakura-bot.net":
                        list = list + "No." + \
                            str(i) + "有効になってないプラグインの動画です\n"
                        i = i + 1
                    else:
                        await que.setdata()
                        list = list + "No." + \
                            str(i) + "[" + que.title + "](" + que.url + ")\n"
                        i = i + 1
                        que.close()
                embed = discord.Embed(
                    title=name, description=list, color=self.bot.Color)
                await ctx.send(embeds=[embed])
                try:
                    while True:
                        d = await self.input(ctx, "削除する曲のNoを数字で入力してください。キャンセルする場合はキャンセルと送ってください")
                        if d.content == "キャンセル":
                            await ctx.send("キャンセルしました")
                            break
                        await cur.execute(
                            "delete FROM `musiclist` where `userid` = %s and `lname` = %s and `id` = %s limit 1",
                            (ctx.author.id, name, res[int(d.content) - 1][3])
                        )
                        await ctx.send("削除しました")
                except SyntaxError:
                    await ctx.send("キャンセルしました")

    @commands.command()
    async def musicranking(self, ctx):
        """
        NLang ja よく聞かれている曲のランキング
        よく聞かれている曲のランキングを表示します。
        **使いかた：**
        EVAL self.bot.command_prefix+'musicranking'
        ELang ja
        NLang default show the ranking of music
        show the ranking of the number of plays
        **how to use：**
        EVAL self.bot.command_prefix+'musicranking'
        ELang default
        """
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `musicranking` ORDER BY `count` desc limit 10")
                res = await cur.fetchall()
                i = 1
                list = ""
                for row in res:
                    que = PluginQueue(restore(row[1]))
                    if que.url == "https://sakura-bot.net":
                        list = list + \
                            str(i) + "位 有効になってないプラグインの動画です\n"
                        i = i + 1
                    else:
                        await que.setdata()
                        list = list + \
                            str(i) + "位 [" + que.title + "](" + que.url + ")\n"
                        i = i + 1
                        que.close()
                embed = discord.Embed(
                    title="よく聞かれている曲", description=list, color=self.bot.Color)
                await ctx.send(embeds=[embed])


class PluginManager:
    def __init__(self, bot, id):
        self.id = id
        self.bot = bot

    async def add_class(self, cls):
        plugin = bot.cogs["Plugin"]
        plugin.plugins[self.id][type(cls).__name__] = cls

    async def load_submodule(self, name: str):
        setup = importlib.import_module(name).setup
        await setup(self.bot, self)

    async def load_extension(self, name: str):
        try:
            await self.bot.load_extension(name)
        except commands.ExtensionAlreadyLoaded:
            await self.bot.reload_extension(name)


class Plugin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot, self.before = bot, ""
        self.plugins = {}
        self.users = {}
        self.guilds = {}

    async def cog_load(self):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""CREATE TABLE if not exists `UserPlugin` (
                                  `UserId` BIGINT PRIMARY KEY NOT NULL DEFAULT 0,
                                  `Plugins` JSON
                                  ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;""")
                await cur.execute("""CREATE TABLE if not exists `GuildPlugin` (
                                  `GuildId` BIGINT PRIMARY KEY NOT NULL DEFAULT 0,
                                  `Plugins` JSON
                                  ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;""")
                await cur.execute("""CREATE TABLE if not exists `Plugins` (
                                  `id` BIGINT NOT NULL AUTO_INCREMENT primary key,
                                  `path` VARCHAR(300) NOT NULL,
                                  `type` VARCHAR(300) NOT NULL DEFAULT 'Public',
                                  `name` VARCHAR(300) NOT NULL,
                                  `description` VARCHAR(300) NOT NULL
                                  ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;""")
        response = await self.bot.execute_sql(
            "SELECT * FROM Plugins;", _return_type="fetchall"
        )
        for row in response:
            name = row[2].replace("/", ".")
            try:
                self.plugins[row[0]] = dict()
                setup = importlib.import_module(name).setup
                await setup(self.bot, PluginManager(self.bot, row[0]))
            except Exception as e:
                print(e)
        response = await self.bot.execute_sql(
            "SELECT * FROM UserPlugin;", _return_type="fetchall"
        )
        for row in response:
            self.users[row[0]] = loads(row[1])
        response = await self.bot.execute_sql(
            "SELECT * FROM GuildPlugin;", _return_type="fetchall"
        )
        for row in response:
            self.guilds[row[0]] = loads(row[1])
        await self.bot.remove_cog("music")
        await bot.add_cog(Music(bot))
        music.Queue = PluginQueue
        music.SearchList = PluginSearchList
        music.restore = restore

    async def input(self, ctx: commands.Context, q: str) -> discord.Message:
        def check(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise asyncio.TimeoutError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout=180.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break

    def get_enable_pulgin(self, user: discord.User | discord.Member, guild: discord.Guild):
        added = dict()
        res = list()
        self.guilds.setdefault(str(guild.id), [])
        self.users.setdefault(str(user.id), [])
        for gp in self.guilds[str(guild.id)]:
            try:
                if not added[gp]:
                    res.append(self.plugins[gp])
                    added[gp] = True
            except BaseException:
                continue
        for up in self.users[str(user.id)]:
            try:
                if not added[up]:
                    res.append(self.plugins[up])
                    added[up] = True
            except BaseException:
                continue
        return res

    @commands.group()
    async def s_plugin(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @s_plugin.command()
    @commands.guild_only()
    async def enable_server(self, ctx: GuildContext, code: str | None = None):
        if code is not None:
            args = code.split(".")
            response = await self.bot.execute_sql(
                "SELECT * FROM Plugins WHERE `id` = %s;",
                (args[0],), _return_type="fetchone"
            )
            second_id = Hashids().encode(ctx.guild.id)
            if response[0][2] == args[2] and second_id == args[1]:
                self.guilds.setdefault(str(ctx.guild.id), [])
                self.guilds[str(ctx.guild.id)].append(args[0])
                await self.bot.execute_sql(
                    """INSERT INTO GuildPlugin VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE GuildId = VALUES(GuildId),
                        Plugins = VALUES(Plugins);""",
                    (ctx.guild.id, dumps(self.guilds[str(ctx.guild.id)]))
                )
                await ctx.send("追加しました")
            else:
                await ctx.send("コードが間違っています")
        else:
            response = await self.bot.execute_sql(
                "SELECT * FROM Plugins WHERE `type`='Public'", _return_type="fetchall"
            )
            ctls = ""
            i = 1
            ebdin = 1
            catebds = []
            for cat in response:
                if len(ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n") > 4000:
                    ebdin = 1
                    evd = discord.Embed(
                        title="プラグイン一覧", description=ctls, color=self.bot.Color)
                    catebds.append(evd)
                    ctls = ""
                ctls = ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n"
                i += 1
                ebdin += 1
            evd = discord.Embed(
                title="プラグイン一覧", description=ctls, color=self.bot.Color)
            catebds.append(evd)
            await ctx.send(embeds=catebds)
            cno = int((await self.input(ctx, "プラグインを選んでナンバーを数値で送信してください")).content)
            self.guilds.setdefault(str(ctx.guild.id), [])
            self.guilds[str(ctx.guild.id)].append(response[cno - 1][0])
            await self.bot.execute_sql(
                """INSERT INTO GuildPlugin VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE GuildId = VALUES(GuildId),
                    Plugins = VALUES(Plugins);""",
                (ctx.guild.id, dumps(self.guilds[str(ctx.guild.id)]))
            )
            await ctx.send("追加しました")

    @s_plugin.command()
    @commands.guild_only()
    async def enable_user(self, ctx: GuildContext, code: str | None = None):
        if code is not None:
            args = code.split(".")
            response = await self.bot.execute_sql(
                "SELECT * FROM Plugins WHERE `id` = %s;",
                (args[0],), _return_type="fetchone"
            )
            second_id = Hashids().encode(ctx.guild.id)
            if response[0][2] == args[2] and second_id == args[1]:
                self.users.setdefault(str(ctx.author.id), [])
                self.users[str(ctx.author.id)].append(args[0])
                await self.bot.execute_sql(
                    """INSERT INTO UserPlugin VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE UserId = VALUES(UserId),
                        Plugins = VALUES(Plugins);""",
                    (ctx.author.id, dumps(self.users[str(ctx.author.id)]))
                )
                await ctx.send("追加しました")
            else:
                await ctx.send("コードが間違っています")
        else:
            response = await self.bot.execute_sql(
                "SELECT * FROM Plugins WHERE `type`='Public'", _return_type="fetchall"
            )
            ctls = ""
            i = 1
            ebdin = 1
            catebds = []
            for cat in response:
                if len(ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n") > 4000:
                    ebdin = 1
                    evd = discord.Embed(
                        title="プラグイン一覧", description=ctls, color=self.bot.Color)
                    catebds.append(evd)
                    ctls = ""
                ctls = ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n"
                i = i + 1
                ebdin = ebdin + 1
            evd = discord.Embed(
                title="プラグイン一覧", description=ctls, color=self.bot.Color)
            catebds.append(evd)
            await ctx.send(embeds=catebds)
            cno = int((await self.input(ctx, "プラグインを選んでナンバーを数値で送信してください")).content)
            self.users.setdefault(str(ctx.author.id), list())
            self.users[str(ctx.author.id)].append(response[cno - 1][0])
            await self.bot.execute_sql(
                """INSERT INTO UserPlugin VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE UserId = VALUES(UserId),
                    Plugins = VALUES(Plugins);""",
                (ctx.author.id, dumps(self.users[str(ctx.author.id)]))
            )
            await ctx.send("追加しました")

    @s_plugin.command()
    @commands.guild_only()
    async def remove_server(self, ctx: GuildContext):
        res = await self.bot.execute_sql(
            "SELECT * FROM Plugins WHERE `type`='Public'", _return_type="fetchall"
        )
        response = []
        for r in res:
            if r[0] in self.guilds[str(ctx.guild.id)]:
                response.append(r)
        ctls = ""
        i = 1
        ebdin = 1
        catebds = []
        for cat in response:
            if len(ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n") > 4000:
                ebdin = 1
                evd = discord.Embed(
                    title="プラグイン一覧", description=ctls, color=self.bot.Color)
                catebds.append(evd)
                ctls = ""
            ctls = ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n"
            i = i + 1
            ebdin += 1
        evd = discord.Embed(
            title="プラグイン一覧", description=ctls, color=self.bot.Color)
        catebds.append(evd)
        await ctx.send(embeds=catebds)
        cno = int((await self.input(ctx, "削除するプラグインを選んでナンバーを数値で送信してください")).content)
        self.guilds.setdefault(str(ctx.guild.id), list())
        self.guilds[str(ctx.guild.id)].remnove(response[cno - 1][0])
        await self.bot.execute_sql(
            """INSERT INTO GuildPlugin VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE UserId = VALUES(GuildId),
                Plugins = VALUES(Plugins);""",
            (ctx.guild.id, dumps(self.guilds[str(ctx.guild.id)]))
        )
        await ctx.send("削除しました")

    @s_plugin.command()
    @commands.guild_only()
    async def remove_user(self, ctx: GuildContext):
        res = await self.bot.execute_sql(
            "SELECT * FROM Plugins WHERE `type`='Public'", _return_type="fetchall"
        )
        response = []
        for r in res:
            if r[0] in self.users[str(ctx.guild.id)]:
                response.append(r)
        ctls = ""
        i = 1
        ebdin = 1
        catebds = []
        for cat in response:
            if len(ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n") > 4000:
                ebdin = 1
                evd = discord.Embed(
                    title="プラグイン一覧", description=ctls, color=self.bot.Color)
                catebds.append(evd)
                ctls = ""
            ctls = ctls + "No." + str(i) + cat[3] + ":" + cat[4] + "\n"
            i = i + 1
            ebdin = ebdin + 1
        evd = discord.Embed(
            title="プラグイン一覧", description=ctls, color=self.bot.Color)
        catebds.append(evd)
        await ctx.send(embeds=catebds)
        cno = int((await self.input(ctx, "削除するプラグインを選んでナンバーを数値で送信してください")).content)
        self.users.setdefault(str(ctx.author.id), list())
        self.users[str(ctx.author.id)].remnove(response[cno - 1][0])
        await self.bot.execute_sql(
            """INSERT INTO UserPlugin VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE UserId = VALUES(UserId),
                Plugins = VALUES(Plugins);""",
            (ctx.author.id, dumps(self.users[str(ctx.author.id)]))
        )
        await ctx.send("削除しました")


async def setup(client) -> None:
    global bot
    bot = client
    await bot.add_cog(Plugin(bot))
