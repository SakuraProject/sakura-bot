from discord.ext import commands
import discord

from utils import Bot, get_webhook


class GlobalChat(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channels_cache = []

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS GlobalChat2 (
                ChannelId BIGINT PRIMARY KEY NOT NULL,
                Name VARCHAR(100) NOT NULL DEFAULT 'main'
            ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4
            COLLATE = utf8mb4_bin;"""
        )
        ids = await self.bot.execute_sql(
            "SELECT ChannelId FROM GlobalChat2;", _return_type="fetchall"
        )
        assert isinstance(ids, tuple)
        self.channels_cache = list(ids)

    @commands.hybrid_group(
        description="グローバルチャットです。",
        aliases=["グローバルチャット", "gc"]
    )
    async def globalchat(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")

    @globalchat.command(
        description="グローバルチャットに接続します。"
    )
    async def create(self, ctx: commands.Context, name: str = "main"):
        try:
            await self.bot.execute_sql(
                "INSERT INTO GlobalChat2 VALUES (%s, %s);",
                (ctx.channel.id, name)
            )
            self.channels_cache.append(ctx.channel.id)
        except:
            return await ctx.reply("すでにグローバルチャットに接続しています！")
        await ctx.reply("グローバルチャットに接続しました。")

    @globalchat.command(
        description="グローバルチャットから切断します。"
    )
    async def remove(self, ctx: commands.Context):
        try:
            await self.bot.execute_sql(
                "DELETE FROM GlobalChat2 WHERE ChannelId = %s;",
                (ctx.channel.id,)
            )
            self.channels_cache.remove(ctx.channel.id)
        except:
            return await ctx.reply("グローバルチャットに接続していません。")
        await ctx.reply("グローバルチャットから切断しました。")

    async def gc_send(self, channel_id: int, message: discord.Message):
        channel = self.bot.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return
        webhook = await get_webhook(channel)
        if channel.guild == message.guild or message.author.discriminator == '0000':
            return

        flfl = [(await attachment.to_file()) for attachment in message.attachments]
        embeds = message.embeds
        if message.reference:
            ref = None
            if message.reference.cached_message:
                ref = message.reference.cached_message
            elif message.reference.message_id:
                rch = message.channel
                ref = await rch.fetch_message(message.reference.message_id)
            if ref:
                reb = discord.Embed(
                    description=ref.clean_content, title="返信先")
                if embeds is None:
                    embeds = list()
                else:
                    embeds = message.embeds.copy()
                embeds.append(reb)

        await webhook.send(
            content=message.content, username=str(message.author),
            avatar_url=message.author.avatar, files=flfl or discord.utils.MISSING,
            embeds=embeds, allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.channels_cache:
            return
        if message.author.bot:
            return

        async def sqler(cursor):
            await cursor.execute(
                "SELECT Name FROM GlobalChat2 WHERE ChannelId = %s;",
                (message.channel.id,)
            )
            response = await cursor.fetchone()
            assert isinstance(response, tuple)
            response: str = response[0][0]
            await cursor.execute(
                "SELECT ChannelId FROM GlobalChat2 WHERE Name = %s;", (response,)
            )
            return await cursor.fetchall()
        response = await self.bot.execute_sql(sqler)

        assert isinstance(response, tuple)
        for resp in response:
            self.bot.loop.create_task(self.gc_send(resp[0], message))


async def setup(bot: Bot):
    await bot.add_cog(GlobalChat(bot))
