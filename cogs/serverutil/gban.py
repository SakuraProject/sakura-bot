from dis import disco
from discord.ext import commands
import discord
import asyncio
from orjson import loads

from utils import Bot, dumps, EmbedsButtonView


class gban(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.gban_cache = []
        self.gban_set_cache = []

    async def cog_load(self):
        csql = """CREATE TABLE if not exists Gban2 (
            UserId BIGINT NOT NULL PRIMARY KEY,
            Reason VARCHAR(2000) NOT NULL, Evidence JSON NOT NULL
        ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"""
        csql1 = """CREATE TABLE if not exists GbanSettings2 (
            GuildId BIGINT NOT NULL PRIMARY KEY
        ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"""

        async def sqler(cursor) -> tuple[tuple, tuple]:
            await cursor.execute(csql)
            await cursor.execute("SELECT UserId FROM Gban2;")
            res1 = await cursor.fetchall()
            await cursor.execute(csql1)
            await cursor.execute("SELECT GuildId FROM GbanSettings2;")
            res2 = await cursor.fetchall()
            return (res1, res2)

        res = await self.bot.execute_sql(sqler)
        self.gban_cache = list(x[0] for x in res[0])
        self.gban_set_cache = list(x[0] for x in res[1])

    @commands.group()
    async def gban(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @gban.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def onoff(self, ctx: commands.Context, onoff: bool):
        assert ctx.guild

        if onoff:
            if ctx.guild.id not in self.gban_set_cache:
                return await ctx.send("すでに設定はオンです！")
            await self.bot.execute_sql(
                "DELETE FROM GbanSettings2 WHERE GuildId = %s;",
                (ctx.guild.id,)
            )
            self.gban_set_cache.remove(ctx.guild.id)
        else:
            if ctx.guild.id in self.gban_set_cache:
                return await ctx.send("すでに設定はオフです！")
            await self.bot.execute_sql(
                "INSERT INTO GbanSettings2 VALUES (%s)",
                (ctx.guild.id,)
            )
            self.gban_set_cache.append(ctx.guild.id)
        await ctx.send("Ok")

    @gban.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, user_id: int, *, reason):
        if user_id in self.gban_cache:
            return await ctx.send("そのユーザーは既に登録されています。")

        if ctx.message.attachments:
            evi = [a.url for a in ctx.message.attachments]
        else:
            evi = []
        evif = dumps(evi)

        for guild in self.bot.guilds:
            if guild.id in self.gban_set_cache:
                continue
            try:
                await guild.ban(discord.Object(user_id), reason=reason + "\nFor Sakura Bot Global BAN")
                await asyncio.sleep(1)
            except discord.NotFound:
                return await ctx.send("ユーザーの取得に失敗しました。")
            except discord.Forbidden:
                continue
            except Exception as e:
                await ctx.send(f"Error `{e}`\nOn {guild.name}({guild.id})")

        await self.bot.execute_sql(
            "INSERT INTO Gban2 VALUES (%s,%s,%s);", (user_id, reason, evif)
        )
        self.gban_cache.append(user_id)
        await ctx.send("追加しました。")

    @gban.command()
    async def list(self, ctx: commands.Context):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM Gban2")
                if (res := await cur.fetchall()) == 0:
                    await ctx.send("gbanされた人はまだいません")
                else:
                    ebds: list[discord.Embed] = list()
                    for r in res:
                        user = self.bot.get_user(r[0])
                        if user is None:
                            uname = "名前が取得出来ませんでした"
                        else:
                            uname = user.name
                        ev = loads(r[2])
                        et = ""
                        for e in ev:
                            et = et + "[証拠](" + e + ")\n"
                        ebd = discord.Embed(
                            title=uname, description="userid:" + str(r[0]) + "\n" + r[1] + "\n" + et)
                        ebds.append(ebd)
                    await EmbedsButtonView(ebds).send(ctx)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id in self.gban_set_cache:
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `GbanSettings2` where `gid` = %s", (str(member.guild.id),))
                res = await cur.fetchall()
                if len(res) != 0:
                    if res[0][1] == "off":
                        return
                await cur.execute("SELECT * FROM `gban` where `userid` = %s", (str(member.id),))
                res = await cur.fetchall()
                if len(res) != 0:
                    await member.ban(reason="Sakura gbanのため")

    async def input(self, ctx: commands.Context, q: str):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
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


async def setup(bot: Bot):
    await bot.add_cog(gban(bot))
