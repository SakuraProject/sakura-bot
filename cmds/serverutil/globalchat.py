from discord.ext import commands
import discord
import asyncio

class globalchat(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""
    async def cog_load(self):
        ctsql = "CREATE TABLE if not exists `globalchat` (`chid` BIGINT NOT NULL, `gcname` VARCHAR(100) NOT NULL DEFAULT 'main') ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)
    @commands.group(
        aliases=["グローバルチャット","gc"]
    )
    async def globalchat(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")
    @globalchat.command()
    async def create(self, ctx, name="main"):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO `globalchat` (`chid`, `gcname`) VALUES (%s, %s);",(str(ctx.channel.id),name))
                await conn.commit()
                await ctx.reply("グローバルチャットに接続しました")

    @globalchat.command()
    async def remove(self, ctx, name="main"):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from globalchat where chid=%s and gcname=%s",(str(ctx.channel.id),name))
                await conn.commit()
                await ctx.reply("グローバルチャットから切断しました")

    async def gcsend(self, id, message):
        channel = self.bot.get_channel(int(id))
        if channel != None:
            webhook=await self.getwebhook(channel)
            if channel.guild.id!=message.guild.id and message.author.discriminator!='0000':
                flfl=None
                for atc in message.attachments:
                  if flfl==None:
                     flfl=list()
                  flfl.append(await atc.to_file())
                embeds = message.embeds
                if message.reference:
                    if message.reference.cached_message:
                        ref = message.reference.cached_message
                    else:
                        rch = message.channel
                        ref = await ch.fetch_message(message.reference.message_id)
                    reb = discord.Embed(description=ref.clean_content,title="返信先")
                    if embeds == None:
                        embeds = list()
                    embeds.append(reb)
                vie = None
                for c in message.components:
                    if vie == None:
                        vie = discord.ui.View
                    vie.add_item(c)
                alm = discord.AllowedMentions.none()
                if vie != None:
                    if flfl==None:
                        await webhook.send(content=message.content.replace('@here','[here]').replace('@everyone','[everyone]'),username=message.author.name+'#'+message.author.discriminator,avatar_url=message.author.avatar,embeds=embeds,view=vie,allowed_mentions=alm)
                    else:
                        await webhook.send(content=message.content.replace('@here','[here]').replace('@everyone','[everyone]'),username=message.author.name+'#'+message.author.discriminator,avatar_url=message.author.avatar,files=flfl,embeds=embeds,view=vie,allowed_mentions=alm)
                else:
                    if flfl==None:
                        await webhook.send(content=message.content.replace('@here','[here]').replace('@everyone','[everyone]'),username=message.author.name+'#'+message.author.discriminator,avatar_url=message.author.avatar,embeds=embeds,allowed_mentions=alm)
                    else:
                        await webhook.send(content=message.content.replace('@here','[here]').replace('@everyone','[everyone]'),username=message.author.name+'#'+message.author.discriminator,avatar_url=message.author.avatar,files=flfl,embeds=embeds,allowed_mentions=alm)


    @commands.Cog.listener()
    async def on_message(self,message):
        gns = "select gcname from globalchat where chid='" + str(message.channel.id) + "'"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(gns)
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    return
                for row in res:
                    gcname = row[0]
                    chs = "select chid from globalchat where gcname='" + str(gcname) + "'"
                    await cur.execute(chs)
                    res1 = await cur.fetchall()
                    for cr in res1:
                        asyncio.ensure_future(self.gcsend(cr[0],message))
    async def getwebhook(self, channel):
        webhooks=await channel.webhooks()
        webhook=discord.utils.get(webhooks,name='sakuraglobal')
        if webhook==None:
           webhook=await channel.create_webhook(name='sakuraglobal')
        return webhook

async def setup(bot):
    await bot.add_cog(globalchat(bot))
