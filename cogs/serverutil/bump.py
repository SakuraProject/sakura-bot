from discord.ext import commands
from discord.ext import tasks
from time import time
import discord
import asyncio


class bump(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""
        self.notifi.start()

    async def cog_load(self):
        ctsql = "CREATE TABLE if not exists `bump` ( `chid` BIGINT NOT NULL,`noftime` VARCHAR(100) NOT NULL,  `type` VARCHAR(45) NOT NULL,`gid` BIGINT NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        ctsql1 = "CREATE TABLE if not exists `bumpset` ( `gid` BIGINT NOT NULL, `type` VARCHAR(100) NOT NULL, `onoff` VARCHAR(45) NOT NULL DEFAULT 'on', `role` BIGINT NOT NULL DEFAULT 0) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)
                await cur.execute(ctsql1)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == 832614051514417202:
            if message.embeds[0].title == "GlowBoard - 色々できるサーバー掲示板":
                if message.embeds[0].description.find("サーバーの表示順位をアップしました!") != -1:
                    nof = time() + 5400
                    await self.save(message, "toss", nof)
                    async with self.bot.pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (message.guild.id, "toss"))
                            res1 = await cur.fetchall()
                            if len(res1) == 0:
                                await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (message.guild.id, "toss", "on"))
                                onoff = "on"
                            else:
                                onoff = res1[0][2]
                            if onoff == "on":
                                ebd = discord.Embed(
                                    color=self.bot.Color, description="tossを確認しました。次回は<t:" + str(int(nof)) + ":R>です。時間になったら通知します")
                                await message.channel.send(embeds=[ebd])
        if message.author.id == 302050872383242240:
            if message.embeds[0].description.find("表示順をアップしたよ") != -1 or message.embeds[0].description.find("Bump done") != -1:
                nof = time() + 7200
                await self.save(message, "bump", nof)
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (message.guild.id, "bump"))
                        res1 = await cur.fetchall()
                        if len(res1) == 0:
                            await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (message.guild.id, "bump", "on"))
                            onoff = "on"
                        else:
                            onoff = res1[0][2]
                        if onoff == "on":
                            ebd = discord.Embed(
                                color=self.bot.Color, description="bumpを確認しました。次回は<t:" + str(int(nof)) + ":R>です。時間になったら通知します")
                            await message.channel.send(embeds=[ebd])
        if message.author.id == 761562078095867916:
            await asyncio.sleep(5)
            message = await message.channel.fetch_message(message.id)
            if "をアップしたよ" in message.embeds[0].fields[0].name:
                nof = time() + 3600
                await self.save(message, "up", nof)
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (message.guild.id, "up"))
                        res1 = await cur.fetchall()
                        if len(res1) == 0:
                            await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (message.guild.id, "up", "on"))
                            onoff = "on"
                        else:
                            onoff = res1[0][2]
                        if onoff == "on":
                            ebd = discord.Embed(
                                color=self.bot.Color, description="upを確認しました。次回は<t:" + str(int(nof)) + ":R>です。時間になったら通知します")
                            await message.channel.send(embeds=[ebd])
        if message.author.id == 716496407212589087:
            if message.content.find("Raised!") != -1:
                nof = time() + 14106
                await self.save(message, "raise", nof)
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (message.guild.id, "raise"))
                        res1 = await cur.fetchall()
                        if len(res1) == 0:
                            await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (message.guild.id, "raise", "on"))
                            onoff = "on"
                        else:
                            onoff = res1[0][2]
                        if onoff == "on":
                            ebd = discord.Embed(
                                color=self.bot.Color, description="rt!raiseを確認しました。次回は<t:" + str(int(nof)) + ":R>です。時間になったら通知します")
                            await message.channel.send(embeds=[ebd])
        if message.author.id == 961521106227974174:
            if message.content.find("Raised!") != -1:
                nof = time() + 14106
                await self.save(message, "frrtraise", nof)
                async with self.bot.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (message.guild.id, "frrtraise"))
                        res1 = await cur.fetchall()
                        if len(res1) == 0:
                            await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (message.guild.id, "frrtraise", "on"))
                            onoff = "on"
                        else:
                            onoff = res1[0][2]
                        if onoff == "on":
                            ebd = discord.Embed(
                                color=self.bot.Color, description="fr!raiseを確認しました。次回は<t:" + str(int(nof)) + ":R>です。時間になったら通知します")
                            await message.channel.send(embeds=[ebd])

    dics = dict()
    dics["toss"] = "tossの時間だよg.tossをして表示順位を上げましょう"
    dics["raise"] = "raiseの時間だよrt!raiseをして表示順位を上げましょう"
    dics["frrtraise"] = "Free RTのraiseの時間だよfr!raiseをして表示順位を上げましょう"
    dics["up"] = "upの時間だよ/dissoku upをして表示順位を上げましょう"
    dics["bump"] = "bumpの時間だよ/bumpをして表示順位を上げましょう"

    @tasks.loop(seconds=10)
    async def notifi(self):
        nti = time()
        sql = "SELECT * FROM `bump`"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                res = await cur.fetchall()
                await conn.commit()
                for row in res:
                    typ = row[2]
                    await cur.execute("SELECT * FROM `bumpset` where `gid`=%s and `type`=%s", (row[3], typ))
                    res1 = await cur.fetchall()
                    if len(res1) == 0:
                        await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`) VALUES (%s,%s,%s);", (row[3], typ, "on"))
                        onoff = "on"
                    else:
                        onoff = res1[0][2]
                    if float(row[1]) <= nti:
                        if onoff == "on":
                            channel = self.bot.get_channel(row[0])
                            if channel is not None:
                                rol = channel.guild.get_role(int(res1[0][3]))
                                ebd = discord.Embed(
                                    title=typ + "通知", color=self.bot.Color, description=self.dics[typ])
                                if rol:
                                    await channel.send(content=rol.mention, embeds=[ebd])
                                else:
                                    await channel.send(embeds=[ebd])
                            await cur.execute("DELETE FROM `bump` where `gid`=%s and `type`=%s", (row[3], typ))

    async def save(self, message, type, nof):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO `bump` (`chid`, `noftime`, `type`, `gid`) VALUES (%s, %s, %s, %s);", (message.channel.id, str(nof), type, message.guild.id))
                await conn.commit()

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def frrtraiseonoff(self, ctx, onoff, role: discord.Role = None):
        if role is None:
            roleid = 0
        else:
            roleid = role.id
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `bumpset` where `type`=%s and `gid` = %s", ("frrtraise", ctx.guild.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`, `role`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, "frrtraise", onoff.replace("true", "on"), roleid))
                else:
                    await cur.execute("UPDATE `bumpset` SET `gid` = %s,`type` = %s,`onoff` = %s,`role` = %s where `gid` = %s and `type` = %s;", (ctx.guild.id, "frrtraise", onoff.replace("true", "on"), roleid, ctx.guild.id, "frrtraise"))
                await ctx.reply("設定しました")

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def raiseonoff(self, ctx, onoff, role: discord.Role = None):
        if role is None:
            roleid = 0
        else:
            roleid = role.id
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `bumpset` where `type`=%s and `gid` = %s", ("raise", ctx.guild.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`, `role`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, "raise", onoff.replace("true", "on"), roleid))
                else:
                    await cur.execute("UPDATE `bumpset` SET `gid` = %s,`type` = %s,`onoff` = %s,`role` = %s where `gid` = %s and `type` = %s;", (ctx.guild.id, "raise", onoff.replace("true", "on"), roleid, ctx.guild.id, "raise"))
                await ctx.reply("設定しました")

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def bumponoff(self, ctx, onoff, role: discord.Role = None):
        if role is None:
            roleid = 0
        else:
            roleid = role.id
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `bumpset` where `type`=%s and `gid` = %s", ("bump", ctx.guild.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`, `role`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, "bump", onoff.replace("true", "on"), roleid))
                else:
                    await cur.execute("UPDATE `bumpset` SET `gid` = %s,`type` = %s,`onoff` = %s,`role` = %s where `gid` = %s and `type` = %s;", (ctx.guild.id, "bump", onoff.replace("true", "on"), roleid, ctx.guild.id, "bump"))
                await ctx.reply("設定しました")

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def tossonoff(self, ctx, onoff, role: discord.Role = None):
        if role is None:
            roleid = 0
        else:
            roleid = role.id
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `bumpset` where `type`=%s and `gid` = %s", ("toss", ctx.guild.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`, `role`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, "toss", onoff.replace("true", "on"), roleid))
                else:
                    await cur.execute("UPDATE `bumpset` SET `gid` = %s,`type` = %s,`onoff` = %s,`role` = %s where `gid` = %s and `type` = %s;", (ctx.guild.id, "toss", onoff.replace("true", "on"), roleid, ctx.guild.id, "toss"))
                await ctx.reply("設定しました")

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def uponoff(self, ctx, onoff, role: discord.Role = None):
        if role is None:
            roleid = 0
        else:
            roleid = role.id
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `bumpset` where `type`=%s and `gid` = %s", ("up", ctx.guild.id))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `bumpset` (`gid`, `type`, `onoff`, `role`) VALUES (%s,%s,%s,%s);", (ctx.guild.id, "up", onoff.replace("true", "on"), roleid))
                else:
                    await cur.execute("UPDATE `bumpset` SET `gid` = %s,`type` = %s,`onoff` = %s,`role` = %s where `gid` = %s and `type` = %s;", (ctx.guild.id, "up", onoff.replace("true", "on"), roleid, ctx.guild.id, "up"))
                await ctx.reply("設定しました")


async def setup(bot):
    await bot.add_cog(bump(bot))
