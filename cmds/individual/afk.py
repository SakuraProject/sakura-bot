from discord.utils import get
import discord
from discord.ext import commands

class afk(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    async def cog_load(self):
        ctsql = "create table if not exists afk (userid BIGINT, vl TEXT);"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)

    @commands.group()
    async def afk(self,ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @afk.command()
    async def set(self,ctx,*,vl):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = "select * from afk where userid='" + str(ctx.author.id) + "';"
                await cur.execute(sql)
                result = await cur.fetchall()
                await conn.commit()
                if len(result) == 0:
                    await cur.execute("INSERT INTO afk (userid, vl) VALUES (%s,%s)",(str(ctx.author.id),vl))
                    await ctx.send("設定しました")
                else:
                    await ctx.send("すでに設定されています")

    @commands.Cog.listener()
    async def on_message(self,message):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = "select * from afk where userid='" + str(message.author.id) + "';"
                await cur.execute(sql)
                result = await cur.fetchall()
                if len(result) == 1:
                    sql = "delete from afk where userid='" + str(message.author.id) + "' limit 1;"
                    await cur.execute(sql)
                    await message.channel.send('afkを解除しました',reference=message)
                sql = "select * from afk;"
                await cur.execute(sql)
                afkresult = await cur.fetchall()
                if len(afkresult) != 0:
                    alist = [int(row[0]) for row in afkresult]
                    cde = [mex for mex in message.mentions]
                    whs = await message.channel.webhooks()
                    wh=discord.utils.get(whs,name='sakurabot')
                    if wh == None:
                        wh = await message.channel.create_webhook(name='sakurabot')
                    for maid in cde:
                        if maid.id in alist:
                            sql = "select * from afk where userid='" + str(maid.id) + "';"
                            await cur.execute(sql)
                            mresult = await cur.fetchall()
                            vl = mresult[0][1]
                            await wh.send(content=vl,username=maid.name+'-留守メッセージ',avatar_url=maid.display_avatar.url)
async def setup(bot):
    await bot.add_cog(afk(bot))