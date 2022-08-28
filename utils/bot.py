# Sakura Utils - Bot

from typing import Any

from discord.ext import commands
from aiohttp import ClientSession
from aiomysql import Pool


__all__ = ["Bot"]

class Bot(commands.Bot):
    "SakuraBotのコアです。"
    session: ClientSession
    pool: Pool
    owner_ids: list[int]

    Color = 0xffbdde

    async def execute_sql(
        self, sql: str, injects: tuple[Any, ...] | None = None, return_type: str = ""
    ):
        "SQL文を実行します。"
        async with self.pool.acquire() as conn:
            async with conn.cursor as cursor:
                await cursor.execute(sql, injects)
                if return_type == "fetchall":
                    return await cursor.fetchall()
                elif return_type == "fetchone":
                    return await cursor.fetchone()
