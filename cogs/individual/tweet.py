import discord
from discord.ext import commands

from tweepy.asynchronous import AsyncStreamingClient
from tweepy import OAuth1UserHandler, Client, StreamRule
from tweepy.errors import NotFound, Forbidden, TweepyException
from tweepy.client import Response
from math import inf

import os

from aiohttp import ClientSession, ClientTimeout
import aiomysql

from utils import Bot


class Tweet(commands.Cog, AsyncStreamingClient):
    @property
    def session(self):
        if self._session.closed:
            self._session = ClientSession(timeout=self.timeout)
        return self._session

    def __init__(self, bot: Bot):
        self.bot = bot
        self.task = None
        handler = OAuth1UserHandler(
            os.environ["TWITTERAPIKEY"], os.environ["TWITTERSECRET"])
        handler.set_access_token(
            os.environ["TWITTERTOKEN"], os.environ["TWITTERTOKENSEC"])
        self.twicon = Client(
            bearer_token=os.environ["TWITTERBEAR"], consumer_key=os.environ["TWITTERAPIKEY"],
            consumer_secret=os.environ["TWITTERSECRET"], access_token=os.environ["TWITTERTOKEN"],
            access_token_secret=os.environ["TWITTERTOKENSEC"])  # API(handler)
        self.api = self.twicon
        self.fil = None
        self.bearer_token = os.environ["TWITTERBEAR"]
        self.consumer_key = os.environ["TWITTERAPIKEY"]
        self.consumer_secret = os.environ["TWITTERSECRET"]
        self.access_token = os.environ["TWITTERTOKEN"]
        self.access_token_secret = os.environ["TWITTERTOKENSEC"]
        self.timeout = ClientTimeout(sock_read=90)
        self._session = ClientSession(timeout=self.timeout)
        self.user_agent = "Python/3.9"
        self.max_retries = inf
        self.proxy = None
        self.return_type = Response
        self.rid: Response = None  # type: ignore
        # super().__init__(consumer_key=os.environ["TWITTERAPIKEY"],consumer_secret=os.environ["TWITTERSECRET"],access_token=os.environ["TWITTERTOKEN"],access_token_secret=os.environ["TWITTERTOKENSEC"])
        # # API(handler)

    async def cog_load(self):
        csql = "CREATE TABLE if not exists `tweet` (`gid` BIGINT NOT NULL,`cid` BIGINT NOT NULL,`twiname` VARCHAR(1000) NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(csql)
        rs = await self.get_rules()
        if rs.data is not None:
            for r in rs.data:
                await self.delete_rules(r.id)
        await self.setfilter()

    async def setrule(self):
        async def sqler(cur: aiomysql.Cursor):
            await cur.execute("SELECT cid,twiname FROM `tweet`")
            result = await cur.fetchall()
            self.fil = []
            filn = []
            for row in result:
                ch = self.bot.get_channel(row[0])
                if not ch or not isinstance(ch, discord.TextChannel):
                    continue
                if not row[1] in filn:
                    try:
                        user = self.twicon.get_user(
                            username=row[1])
                        if user.data is None:
                            await ch.send("通知を試みましたがユーザーが見つかりませんでした。")
                            await cur.execute("delete FROM `tweet` where `cid`=%s and `twiname`=%s", (row[0], row[1]))
                        else:
                            twiid = user.data.username
                            filn.append(row[1])
                            if not twiid in self.fil:
                                self.fil.append(twiid)
                    except NotFound:
                        await ch.send("通知を試みましたがユーザーが見つかりませんでした。")
                        await cur.execute("delete FROM `tweet` where `cid`=%s and `twiname`=%s", (row[0], row[1]))
                    except Forbidden:
                        await ch.send("通知を試みましたが情報の取得に失敗しました")
            rtext = ""
            for name in self.fil:
                if rtext != "":
                    rtext = rtext + " OR "
                rtext = rtext + "from:" + name
            # type: ignore
            self.rid = await self.add_rules(StreamRule(rtext))
        await self.bot.execute_sql(sqler)

    async def setfilter(self):
        await self.setrule()
        try:
            self.filter(user_fields="username,profile_image_url",
                        tweet_fields="referenced_tweets,text,id", expansions="author_id")
        except TweepyException:
            str("error")

    async def on_tweet(self, tweet):
        user = self.api.get_user(
            id=tweet.author_id, user_fields="username,profile_image_url").data
        twiname = user.username
        image = user.profile_image_url
        if tweet.referenced_tweets is not None:
            if tweet.referenced_tweets[0].type == "quoted":
                tweet.text = twiname + " ReTweeted [This Tweet](https://twitter.com/" + self.api.get_user(id=self.api.get_tweet(tweet.referenced_tweets[0].id, user_fields="username",
                                                                                                                                expansions="author_id").data.author_id, user_fields="username,profile_image_url").data.username + "/status/" + str(tweet.referenced_tweets[0].id) + ")\n" + tweet.text
            tweet.text = tweet.text.replace(
                "RT @", twiname + " ReTweeted @", 1)
            if tweet.referenced_tweets[0].type == "replied_to":
                tweet.text = twiname + " Reply to [This Tweet](https://twitter.com/" + self.api.get_user(id=self.api.get_tweet(tweet.referenced_tweets[0].id, user_fields="username",
                                                                                                                               expansions="author_id").data.author_id, user_fields="username,profile_image_url").data.username + "/status/" + str(tweet.referenced_tweets[0].id) + ")\n" + tweet.text
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT cid,twiname FROM `tweet` where `twiname`=%s", (twiname,))
                result = await cur.fetchall()
                for row in result:
                    ch = self.bot.get_channel(row[0])
                    if ch is not None:
                        try:
                            wh = await self.getwebhook(ch)
                            await wh.send(tweet.text, username=twiname, avatar_url=image)
                        except Exception as e:
                            print(e)
                            continue

    async def on_status(self, status):
        twiname = status.user.screen_name
        print(status)
        if status.is_quote_status:
            status.text = twiname + " ReTweeted [This Tweet](https://twitter.com/" + status.quoted_status.user.screen_name + \
                "/status/" + status.quoted_status.user.id_str + ")\n" + status.text
        status.text = status.text.replace("RT @", twiname + " ReTweeted @", 1)
        if hasattr(status, "in_reply_to_status_id"):
            if status.in_reply_to_status_id:
                status.text = twiname + " Reply to [This Tweet](https://twitter.com/" + status.in_reply_to_screen_name + \
                    "/status/" + status.in_reply_to_status_id_str + ")\n" + status.text
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT cid,twiname FROM `tweet` where `twiname`=%s", (twiname,))
                result = await cur.fetchall()
                for row in result:
                    ch = self.bot.get_channel(int(row[0]))
                    if ch is not None:
                        try:
                            wh = await self.getwebhook(ch)
                            await wh.send(status.text, username=status.user.screen_name,
                                          avatar_url=status.user.default_profile_image)
                        except Exception:
                            continue

    async def getwebhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name='sakurabot')
        if webhook is None:
            webhook = await channel.create_webhook(name='sakurabot')
        return webhook

    @commands.group()
    async def tweet(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @commands.has_permissions(manage_channels=True, manage_webhooks=True)
    @tweet.command()
    async def set(self, ctx: commands.Context, *, name):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from `tweet` where twiname=%s and cid=%s;", (name, ctx.channel.id))
                result = await cur.fetchall()
                await conn.commit()
                if len(result) == 0:
                    await cur.execute("INSERT INTO `tweet` (gid, cid, twiname) VALUES (%s,%s,%s)", (ctx.guild.id, ctx.channel.id, name))
                    await ctx.send("設定しました")
                    if self.rid.data is not None:
                        await self.delete_rules(ids=self.rid.data[0].id)
                    else:
                        try:
                            await self.delete_rules(ids=self.rid.errors[0]["id"])
                        except KeyError:
                            str("初めて通知設定されたとき")
                    await self.setfilter()
                else:
                    await ctx.send("すでに設定されています")

    @commands.has_permissions(manage_channels=True, manage_webhooks=True)
    @tweet.command()
    async def remove(self, ctx: commands.Context, *, name):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from `tweet` where twiname=%s and cid=%s limit 1;", (name, ctx.channel.id))
                await ctx.send("削除しました")
                if self.rid.data is not None:
                    await self.delete_rules(ids=self.rid.data[0].id)
                else:
                    try:
                        await self.delete_rules(ids=self.rid.errors[0]["id"])
                    except KeyError:
                        str("通知設定がまだされてないとき")
                await self.setfilter()


async def setup(bot: Bot):
    await bot.add_cog(Tweet(bot))
