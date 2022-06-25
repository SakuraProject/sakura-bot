from discord.ext import commands
import discord
import asyncio
from ujson import loads,dumps

class gban(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    async def cog_load(self):
        csql = "CREATE TABLE if not exists `gban` (`userid` BIGINT NOT NULL,`reason` VARCHAR(2000) NOT NULL,`evidence` JSON NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        csql1 = "CREATE TABLE if not exists `gbanset` (`gid` BIGINT NOT NULL,`onoff` VARCHAR(3) NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(csql)
                await cur.execute(csql1)

    @commands.group()
    async def gban(self,ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @gban.command()
    @commands.has_permissions(administrator=True)
    async def onoff(self, ctx):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `gbanset` where `gid` = %s",(str(ctx.guild.id),))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `gbsnset` (`gid`, `onoff`, `role`) VALUES (%s,,%s);",(str(ctx.guild.id),onoff.replace("true","on")))
                else:
                    await cur.execute("UPDATE `gbanset` SET `gid` = %s,`onoff` = %s,`role` = %s where `gid` = %s;",(str(ctx.guild.id),onoff.replace("true","on"),str(roleid),str(ctx.guild.id)))
                await ctx.reply("設定しました")

    @gban.command()
    @commands.is_owner()
    async def add(self, ctx, user_id: int, *, reason):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `gban` where `userid` = %s",(str(user_id),))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) != 0:
                    await ctx.send("そのユーザーはすでに登録されています")
                    return
                if ctx.message.attachments:
                    evi = [a.url for a in ctx.message.attachments]
                else:
                    try:
                        mes = await self.input(ctx,"証拠画像を送信してください")
                        evi = [a.url for a in mes.attachments]
                    except SyntaxError:
                        await ctx.send("キャンセルしました")
                        return
                evif = dumps(evi)
                for g in self.bot.guilds:
                    await cur.execute("SELECT * FROM `gbanset` where `gid` = %s",(str(g.id),))
                    res = await cur.fetchall()
                    await conn.commit()
                    if len(res) != 0:
                        if res[1] == "off":
                            continue
                    await g.ban(await self.bot.fetch_user(user_id),reason="sakura gbanのため")
                    await asyncio.sleep(1)
                await cur.execute("INSERT INTO `gban` (`userid`,`reason`,`evidence`) VALUES (%s,%s,%s);",(str(user_id),reason,evif))
                await ctx.send("完了しました")

    @gban.command()
    async def list(self,ctx):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `gban`")
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await ctx.send("gbanされた人はまだいません")
                else:
                    ebds=list()
                    for r in res:
                        user = self.bot.get_user(r[0])
                        if user == None:
                            uname = "名前が取得出来ませんでした"
                        else:
                            uname = user.name
                        ev = loads(r[2])
                        et = ""
                        for e in ev:
                            et = et + "[証拠](" + e + ")\n"
                        ebd = discord.Embed(title=uname,description="userid:" + str(r[0]) + "\n" + row[1] + "\n" + et)
                        ebds.append(ebd)
                    await ctx.send(embeds=[ebds[0]],view=NextButton(ebds))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `gbanset` where `gid` = %s",(str(member.id),))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) != 0:
                    if res[1] == "off":
                        return
                await cur.execute("SELECT * FROM `gban` where `userid` = %s",(str(user_id),))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) != 0:
                    await member.ban(reason="Sakura gbanのため")

    async def input(self,ctx,q):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await client.wait_for('message', timeout= 180.0, check= check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await client.wait_for('message', timeout= 180.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break
class NextButton(discord.ui.View):
    def __init__(self, ebds):
        self.it = ebds
        self.page = 0

    @discord.ui.button(label="<")
    async def left(self, interaction: discord.Interaction):
        if self.page != 0:
            self.page = self.page -1
            await interaction.response.edit_message(embeds=[self.it[self.page]],view=self)
        else:
            return await interaction.response.send_message("このページが最初です", ephemeral=True)
    @discord.ui.button(label=">")
    async def right(self, interaction: discord.Interaction):
        if self.page != len(self.it) - 1:
            self.page = self.page + 1
            await interaction.response.edit_message(embeds=[self.it[self.page]],view=self)
        else:
            return await interaction.response.send_message("次のページはありません", ephemeral=True)
async def setup(bot):
    await bot.add_cog(gban(bot))