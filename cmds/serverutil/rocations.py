from discord.ext import commands
import discord
from time import time

class rocations(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    async def cog_load(self):
        ctsql="CREATE TABLE if not exists `rocations` ( `gid` BIGINT NOT NULL, `name` VARCHAR(1000) NOT NULL, `description` VARCHAR(1000) NOT NULL, `link` VARCHAR(300) NOT NULL, `category` VARCHAR(100) NOT NULL,`icon` VARCHAR(300) NULL,`uptime` BIGINT NOT NULL DEFAULT 0 ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)

    @commands.group()
    async def serverads(self,ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @serverads.command()
    @commands.has_guild_permissions(administrator=True)
    async def register(self,ctx):
        try:
            await ctx.,send("サーバー登録を開始します。質問を行いますので、質問に回答してくださいね。^^")
            desc = (await self.input(ctx,"このサーバーの説明を入力してください。")).content
            cat = (await self.input(ctx,"カテゴリーを,区切りで入力してください(例:ゲーム,VC,雑談)")).content
            invite = await ctx.channel.create_invite(reason="サーバー掲示板登録のため")
            icon = ctx.guild.icon.url
            gid = ctx.guild.id
            name = ctx.guild.name
            up = int(time())
            async with self.bot.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM `rocations` where `gid`=%s",(ctx.guild.id,))
                    res = await cur.fetchall()
                    await conn.commit()
                    if len(res) == 0:
                        await cur.execute("INSERT INTO `rocations` (`gid`, `name`, `description`, `link`, `category`, `icon`, `uptime`) VALUES (%s,%s,%s,%s,%s,%s,%s);",(gid,name,desc,invite,cat,icon,up))
                    else:
                        await cur.execute("UPDATE `rocations` SET `name` = %s,`description` = %s,`link` = %s,`category` = %s, `icon` = %s where `gid` = %s",(name,desc,invite,cat,icon,gid))
                    await ctx.send("登録完了しました")
        except SyntaxError:
            await ctx.send("キャンセルされました")

    @commands.command()
    async def push(self,ctx):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `rocations` where `gid`=%s",(ctx.guild.id,))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await ctx.reply("このコマンドを使用するにはserverads registerコマンドでサーバーを登録する必要があります")
                else:
                    oldup = int(res[0][6])
                    now = int(time())
                    dt = now - oldup
                    if dt < 7200:
                        await ctx.send("まだpush出来ません。次回は<t:" + str(int(oldup + 7200)) + ":R>です")
                    else:
                        await cur.execute("UPDATE `rocations` SET `uptime` = %s where `gid` = %s",(now,gid))
                        await ctx.send("pushed!掲示板の表示順位を上げました。次回は<t:" + str(int(now + 7200)) + ":R>です")
                    
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

async def setup(bot):
    await bot.add_cog(rocations(bot))