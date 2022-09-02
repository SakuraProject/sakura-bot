import asyncio
from hashids import Hashids
from discord.ext import commands
import discord
from ujson import loads, dumps
import datetime
import random


class giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    async def cog_load(self):
        ctsql = "CREATE TABLE if not exists `giveaway` (`id` VARCHAR(100) NOT NULL,`cid` JSON NOT NULL,`mid` JSON NOT NULL,`end` VARCHAR(200) NOT NULL,`price` VARCHAR(1000) NOT NULL,`author` VARCHAR(100) NOT NULL,`win` VARCHAR(100) NOT NULL,PRIMARY KEY (`id`)) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)
                await conn.commit()
                loadsql = "SELECT * FROM `giveaway`"
                await cur.execute(loadsql)
                res = await cur.fetchall()
                await conn.commit()
                self.gavs = dict()
                for row in res:
                    self.gavs[row[0]] = dict()
                    self.gavs[row[0]]["prize"] = row[4]
                    self.gavs[row[0]]["end"] = int(row[3])
                    self.gavs[row[0]]["cid"] = loads(row[1])
                    self.gavs[row[0]]["mid"] = loads(row[2])
                    self.gavs[row[0]]["author"] = row[5]
                    self.gavs[row[0]]["win"] = row[6]
        asyncio.ensure_future(self.runtensec())

    async def runtensec(self):
        while True:
            try:
                now = int(datetime.datetime.now().timestamp())
                for gk in self.gavs:
                    gaway = self.gavs[gk]
                    endgv = int(gaway['end'])
                    if endgv < now:
                        users = list()
                        for i in range(len(gaway['cid'])):
                            try:
                                new_message = None
                                channel = self.bot.get_channel(
                                    int(gaway['cid'][str(i)]))
                                if channel != None:
                                    try:
                                        new_message = await channel.fetch_message(int(gaway['mid'][str(i)]))
                                    except discord.errors.NotFound:
                                        str('no message')
                            except KeyError:
                                str("keyerror")
                            if channel != None:
                                if new_message != None:
                                    userstemp = [u async for u in new_message.reactions[0].users()]
                                    try:
                                        userstemp.pop(
                                            users.index(self.bot.user))
                                    except:
                                        str('poperror')
                                        users.extend(userstemp)
                                ufc = 0
                                for u in users:
                                    if u.id == self.bot.user.id:
                                        users.pop(ufc)
                                        ufc = ufc-1
                                    ufc = ufc+1
                                # users.pop(users.index(self.bot.user))
                        win = int(gaway['win'])
                        prize = gaway['prize']
                        if len(users) == 0:
                            winner = 'No users'
                        else:
                            wusgiv = random.choice(users)
                            wusgivt = wusgiv.name+'#'+wusgiv.discriminator
                            winner = wusgiv.mention+'('+wusgivt+')'
                            for i in range(win-1):
                                wusgiv = random.choice(users)
                                wusgivt = wusgiv.name+'#'+wusgiv.discriminator
                                winner = winner+',' + \
                                    wusgiv.mention+'('+wusgivt+')'
                            for i in range(len(gaway['cid'])):
                                winning_announcement = discord.Embed(
                                    color=0xff2424)
                                winning_announcement.set_author(
                                    name=f'THE GIVEAWAY HAS ENDED!', icon_url='https://i.imgur.com/DDric14.png')
                                winning_announcement.add_field(
                                    name=f'🎉 景品: {prize}', value=f'🥳 **勝者**: {winner}\n 🎫  **参加者数**: {len(users)}', inline=False)
                                winning_announcement.set_footer(
                                    text='Thanks for entering!')
                                channelt = self.bot.get_channel(
                                    int(gaway['cid'][str(i)]))
                                if channelt != None:
                                    await channelt.send(embed=winning_announcement)
                                self.gavs.pop(gk)
                                await self.delete(gk)
            except RuntimeError:
                str('continue')
            except IndexError:
                str('continue')
            await asyncio.sleep(10)

    async def delete(self, gv):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from `giveaway` where `id`=%s", (gv))
                await conn.commit()

    async def save(self, gv):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from `giveaway` where `id`=%s", (gv))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `gombot`.`giveaway` (`id`, `cid`, `mid`, `end`, `price`, `author`,`win`) VALUES (%s, %s, %s, %s, %s, %s, %s);", (gv, dumps(self.gavs[gv]["cid"]), dumps(self.gavs[gv]["mid"]), str(self.gavs[gv]["end"]), self.gavs[gv]["prize"], self.gavs[gv]["author"], self.gavs[gv]["win"]))
                else:
                    await cur.execute("UPDATE `giveaway` SET `cid` = %s, `mid` = %s, `end` = %s, `price` = %s, `author` = %s, `win` = %s WHERE (`id` = %s);", (dumps(self.gavs[gv]["cid"]), dumps(self.gavs[gv]["mid"]), str(self.gavs[gv]["end"]), self.gavs[gv]["prize"], self.gavs[gv]["author"], self.gavs[gv]["win"], gv))
                await conn.commit()

    @commands.group(aliases=["抽選"])
    async def giveaway(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @giveaway.command()
    async def join(self, ctx, code):
        giveaway_questions = ['どのチャンネルで開催する?', ]
        giveaway_answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

            # Askes the questions from the giveaway_questions list 1 by 1
            # Times out if the host doesn't answer within 30 seconds
        for question in giveaway_questions:
            await ctx.channel.send(question)
            try:
                message = await self.bot.wait_for('message', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                giveaway_answers.append(message.content)
        try:
            c_id = int(giveaway_answers[0][2:-1])
        except:
            await ctx.channel.send(f'チャンネルメンションが無効だよ。このように入力してね: {ctx.channel.mention}')
            return
        channel = self.bot.get_channel(c_id)
        try:
            jself.gavs = self.gavs[code]
            prize = jself.gavs['prize']
            author = jself.gavs['author']
            endstr = datetime.datetime.fromtimestamp(
                int(jself.gavs['end'])).strftime('%Y/%m/%d %H:%M')
            give = discord.Embed(color=0x2ecc71)
            give.set_author(name=f'GIVEAWAY TIME!',
                            icon_url='https://i.imgur.com/VaX0pfM.png')
            give.add_field(name=f'{author}が開催した抽選: {prize}!',
                           value=f'🎉を押して参加!\n 終了時刻{endstr}!', inline=False)
            my_message = await channel.send(embed=give)
            await my_message.add_reaction("🎉")
            self.gavs[code]['cid'][str(
                len(self.gavs[code]['cid']))] = channel.id
            self.gavs[code]['mid'][str(
                len(self.gavs[code]['mid']))] = my_message.id
            await self.save(code)
        except KeyError:
            await ctx.send(f'招待コードが無効です')

    @giveaway.command()
    async def create(self, ctx):
        giveaway_questions = ['どのチャンネルで開催する?',
                              '景品は何にする?', 'Giveawayは何秒間開催する？', '当選者は何人にする？', ]
        giveaway_answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        for question in giveaway_questions:
            await ctx.channel.send(question)
            try:
                message = await self.bot.wait_for('message', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
                return
            else:
                giveaway_answers.append(message.content)
        try:
            c_id = int(giveaway_answers[0][2:-1])
        except:
            await ctx.channel.send(f'チャンネルメンションが無効だよ。このように入力してね: {ctx.channel.mention}')
            return
        channel = self.bot.get_channel(c_id)
        prize = str(giveaway_answers[1])
        times = int(giveaway_answers[2])
        win = int(giveaway_answers[3])
        await ctx.channel.send(f'{prize}の抽選を開始しました\n{channel.mention}でお知らせをしてください、開催期間は{times}秒です')
        give = discord.Embed(color=0x2ecc71)
        give.set_author(name=f'GIVEAWAY TIME!',
                        icon_url='https://i.imgur.com/VaX0pfM.png')
        give.add_field(name=f'{ctx.author.name}が開催した抽選: {prize}!',
                       value=f'🎉を押して参加!\n 終了時刻{round(times/60/60, 2)}時間!', inline=False)
        end = datetime.datetime.utcnow() + datetime.timedelta(seconds=times)
        give.set_footer(text=f'Giveaway ends at {end} UTC!')
        my_message = await channel.send(embed=give)
        await my_message.add_reaction("🎉")
        hashids = Hashids()
        id = hashids.encode(c_id)
        idt = id
        igvi = 1
        while True:
            if idt in self.gavs.keys():
                idt = id+'_'+str(igvi)
                igvi = igvi+1
            else:
                break
        id = idt
        self.gavs[id] = {
            "end": int(datetime.datetime.now().timestamp())+times,
            "win": win,
            "cid": {"0": channel.id},
            "mid": {"0": my_message.id},
            "prize": prize,
            "author": ctx.author.name
        }
        await ctx.author.send(f'Giveaway連携コードは{id}です。ほかのサーバーでも同時開催したいときに使ってね')
        await self.save(id)


async def setup(bot):
    await bot.add_cog(giveaway(bot))
