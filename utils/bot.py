# Sakura Utils - Bot

from typing import Callable

from inspect import iscoroutinefunction

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
        self, sql: str | Callable,
        _injects: tuple | None = None, _return_type: str = "",
        **kwargs
    ):
        "SQL文を実行します。"

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if iscoroutinefunction(sql):
                    return await sql(cursor, **kwargs)
                elif callable(sql):
                    raise ValueError("sql parameter must be async function.")
                await cursor.execute(sql, _injects)
                if _return_type == "fetchall":
                    return await cursor.fetchall()
                elif _return_type == "fetchone":
                    return await cursor.fetchone()
