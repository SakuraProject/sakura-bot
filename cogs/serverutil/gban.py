# Sakura Bot - Global BAN

import asyncio

from discord.ext import commands
import discord

from orjson import loads

from utils import Bot, dumps, EmbedsButtonView


class Gban(commands.Cog):
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

    @commands.hybrid_group(description="GBAN機能です。")
    async def gban(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @gban.command(description="GBANのオンオフを切り替えます。")
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

    @gban.command(with_app_command=False)
    @commands.is_owner()
    async def add(self, ctx: commands.Context, user_id: int, *, reason):
        if user_id in self.gban_cache:
            return await ctx.send("そのユーザーは既に登録されています。")

        if ctx.message.attachments:
            evi = [a.url for a in ctx.message.attachments]
        else:
            evi = []
        evif = dumps(evi)
        await ctx.send("BANを開始します...")

        for guild in self.bot.guilds:
            if guild.id in self.gban_set_cache:
                continue
            try:
                await guild.ban(discord.Object(user_id),
                    reason=reason + "\nFor Sakura Bot Global BAN")
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

    @gban.command(description="GBANされたユーザーの一覧を表示します。")
    async def list(self, ctx: commands.Context):
        await ctx.typing()
        res = await self.bot.execute_sql(
            "SELECT * FROM Gban2", _return_type="fetchall"
        )
        if not res:
            await ctx.send("gbanされた人はまだいません")
        else:
            ebds: list[discord.Embed] = []
            for row in res:
                user = self.bot.get_user(row[0])
                uname = getattr(user, "name", "名前が取得できませんでした。")
                et = ""
                for index, item in enumerate(loads(row[2])):
                    et += f"[証拠画像{index}]({item})\n"
                ebd = discord.Embed(
                    title=uname,
                    description=f"userid:{row[0]}\n{row[1]}\n{et}"
                )
                ebds.append(ebd)
            await EmbedsButtonView(ebds).send(ctx)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id in self.gban_set_cache:
            return
        if member.id not in self.gban_cache:
            return
        (row,) = await self.bot.execute_sql(
            "SELECT * FROM Gban2 WHERE UserId = %s;", (member.id,),
            _return_type="fetchone"
        )
        try:
            await member.ban(reason=row[1] + "\nFor Sakura Global BAN.")
        except discord.Forbidden:
            try:
                await member.guild.owner.send(  # type: ignore
                    f"GlobalBANされたユーザー: {member.mention}が"
                    f"{member.guild.name}に入室しましたがBANできませんでした。"
                    "権限を確認してください。"
                )
            except (AttributeError, discord.HTTPException):
                pass


async def setup(bot: Bot):
    await bot.add_cog(Gban(bot))
