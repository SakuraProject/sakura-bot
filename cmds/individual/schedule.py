from discord.ext import commands, tasks
from discord import app_commands
import discord
from datetime import datetime
from asyncio import Event


class schedule(commands.Cog): 

    def __init__(self, bot): 
        self.bot = bot
        self.cache = dict()
        self.ready = Event()
        self.pool = self.bot.pool
        self.process_notice.start()

    async def _prepare_table(self):
        # テーブルの準備をする。このクラスのインスタンス化時に自動で実行される。
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"""CREATE TABLE IF NOT EXISTS schedule (
                        UserID BIGINT NOT NULL, body TEXT, stime TEXT, etime TEXT, day TEXT, dmnotice VARCHAR(3)
                    );"""
                )
                # キャッシュを用意しておく。
                await cursor.execute(f"SELECT * FROM schedule;")
                for row in await cursor.fetchall():
                    if row and row[1]: 
                        try: 
                            self.cache[row[0]][row[1]] = {
                                'UserID': row[0], 'body': row[1], 'stime': row[2], 'etime': row[3], 'day': row[4], 'dmnotice': row[5]}
                        except KeyError:
                            self.cache[row[0]] = dict()
                            self.cache[row[0]][row[1]] = {
                                'UserID': row[0], 'body': row[1], 'stime': row[2], 'etime': row[3], 'day': row[4], 'dmnotice': row[5]}

    async def cog_load(self):
        await self._prepare_table()

    @commands.hybrid_group(
        aliases=["予定", "sch"]
    )
    async def schedule(self, ctx: commands.Context): 
        if not ctx.invoked_subcommand: 
            await ctx.reply("使用方法が違います。")

    @schedule.command(
        "set", aliases=["s", "設定"],
        extras={
            "headding": {
                "ja": "予定を設定します。",
                "en": "Set schedule"
            }
        }
    )
    @app_commands.describe(start="予定開始時間", end="予定終了時間", day="日付", notice="DM通知するかどうか", title="タイトル")
    async def set_(self, ctx: commands.Context, start, end, day, notice: bool, *, title): 
        notice = "on" if notice else "off"
        await ctx.typing()
        await self.set_schedule(ctx.author.id, start, end, day, notice, title)
        await ctx.reply("Ok")

    @schedule.command(
        aliases=["del", "削除"]
    )
    @app_commands.describe(title="予定のタイトル")
    async def delete(self, ctx: commands.Context, *, title):
        try:
            await self.delete_schedule(ctx.author.id, title)
        except AssertionError:
            await ctx.reply(
                "その予定が見つかりませんでした。"
            )
        except KeyError:
            await ctx.reply(
                "その予定が見つかりませんでした。"
            )
        else:
            await ctx.reply("Ok")

    @tasks.loop(seconds=10)
    async def process_notice(self):
        try:
            await self.ready.wait()
            now = datetime.now()
            now = now.strftime("%Y/%m/%d%H:%M")

            if self.before != now:
                self.before = now

                for user_id, datas in list(self.cache.items()):
                    for title, data in datas.items():
                        if data['day'] + data['stime'] == now:
                            if (user := self.bot.get_user(user_id)):
                                if data['dmnotice'] == "on":
                                    await user.send("予定のお時間です\n予定:" + title)
                            else:
                                # もしユーザーが見つからなかったのならそのデータを削除する。
                                await self.delete(user_id)
                        if data['day'] + data['etime'] == now:
                            try:
                                await self.delete_schedule(user_id, title)
                            except AssertionError:
                                len('test')
        except Exception:
            datetime.now()

    async def delete_schedule(self, userid, data) -> None:
        for title, d in self.cache[userid].items():
            if title == data:
                del self.cache[userid][title]
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            f"""DELETE FROM schedule
                                WHERE UserID = %s AND body = %s;""",
                            (userid, title)
                        )
                break
        else:
            assert False, "その予定は設定されていません。"

    @schedule.command(
        "list", aliases=["l", "一覧"]
    )
    async def list_(self, ctx: commands.Context):
        try:
            data = self.cache[ctx.author.id]
            embed = discord.Embed(
                title=self.__cog_name__, color=self.bot.Color
            )
            days = dict()
            for body, d in data.items():
                try:
                    days[d['day']].append(d)
                except KeyError:
                    days[d['day']] = list()
                    days[d['day']].append(d)
            sdays = sorted(days.items(), key=lambda x: x[0])
            for dal in sdays:
                val = ""
                for dt in dal[1]:
                    val = val + dt['stime'] + "~" + dt['etime'] + '\n' + dt['body'] + "\n"
                embed.add_field(
                    name=dal[0],
                    value=val
                )
            await ctx.reply(embed=embed)
        except KeyError:
            await ctx.reply("予定はありません")

    async def set_schedule(self, userid, start, end, day, notice, title: str = None) -> None:
        if title:
            try:
                self.cache[userid][title] = dict()
            except KeyError:
                self.cache[userid] = dict()
                self.cache[userid][title] = dict()
            m = {'stime': start, 'etime': end, 'day': day, 'dmnotice': notice, 'body': title}
            self.cache[userid][title].update(m)
        elif userid in self.cache:
            del self.cache[userid]
        if title is None:
            title = ""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"INSERT INTO schedule VALUES (%s, %s, %s, %s, %s, %s);",
                    (userid, title, start, end, day, notice)
                )

    def cog_unload(self):
        self.process_notice.cancel()


async def setup(bot):
    await bot.add_cog(schedule(bot))
