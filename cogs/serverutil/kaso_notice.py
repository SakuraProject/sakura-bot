# Sakura bot - 過疎化通知

from discord.ext import commands, tasks
from discord import app_commands
import discord

from utils import Bot


class KasoNotice(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache = {}

    async def cog_load(self) -> None:
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS KasoNotice (
                ChannelId BIGINT PRIMARY KEY NOT NULL,
                Deadline INT
            );"""
        )
        cache = await self.bot.execute_sql(
            "SELECT * FROM KasoNotice;", _return_type="fetchall"
        )
        assert isinstance(cache, tuple)
        self.cache = {c[0]: c[1] for c in cache}

    @commands.hybrid_command(
        description="過疎化通知を設定します。",
        aliases=("kasonotice", "過疎通知", "過疎化通知", "kaso_tuuti")
    )
    @app_commands.describe(deadline="何分過疎化したら通知するか。")
    async def kaso_notice(self, ctx: commands.Context, deadline: int):
        self.cache[ctx.channel.id] = deadline
        await self.bot.execute_sql(
            "INSERT INTO KasoNotice VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE Deadline = %s",
            (ctx.channel.id, deadline, deadline)
        )

    @tasks.loop(minutes=1)
    async def check_kaso_loop(self):
        for ch_id in self.cache.keys():
            channel = self.bot.get_channel(ch_id)
            if not channel or not isinstance(
                channel, discord.TextChannel | discord.Thread
            ):
                del self.cache[ch_id]
                await self.bot.execute_sql(
                    "DELETE FROM KasoNotice WHERE ChannelId = %s",
                    (ch_id,)
                )
                continue
            if not channel.last_message_id:
                continue
            last_datetime = discord.utils.snowflake_time(
                channel.last_message_id)
            if self.cache[ch_id] < (
                    discord.utils.utcnow() - last_datetime).seconds // 60:
                # 通知
                await channel.send(
                    f"過疎化通知です。前回のメッセージ送信から{self.cache[ch_id]}分経ちました。"
                    "\n会話をしてチャンネルを盛り上げましょう。"
                )


async def setup(bot: Bot):
    await bot.add_cog(KasoNotice(bot))
