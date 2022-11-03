# Sakura Utils - Bot

from typing import TypeVar, Any, Callable, Literal, overload
from collections.abc import Coroutine

from inspect import iscoroutinefunction

from discord.ext import commands
from aiohttp import ClientSession
from aiomysql import Pool
from orjson import loads

from ._types import Cogs


reT = TypeVar("reT")


class Bot(commands.Bot):
    "SakuraBotのコアです。"

    _session: ClientSession | None
    pool: Pool
    owner_ids: list[int]
    cogs: Cogs

    Color = 0xffbdde

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None

    @property
    def session(self) -> ClientSession:
        if not self._session or self._session.closed:
            self._session = ClientSession(loop=self.loop, json_serialize=loads)
        return self._session

    @overload
    async def execute_sql(
        self, sql: str, _injects: tuple | None = None,
        _return_type: Literal["fetchall", "fetchone", ""] = ""
    ) -> tuple[tuple, ...]:
        ...
    @overload
    async def execute_sql(
        self, sql: str, _injects: tuple | None = None,
        _return_type: Literal[""] = ""
    ) -> tuple:
        ...
    @overload
    async def execute_sql(
        self, sql: Callable[..., Coroutine[Any, Any, reT]],
        _injects: None = None, _return_type: Literal[""] = "", **kwargs
    ) -> reT:
        ...

    async def execute_sql(
        self, sql: str | Callable[..., Coroutine[Any, Any, reT]],
        _injects: tuple | None = None,
        _return_type: Literal["fetchall", "fetchone", ""] = "",
        **kwargs
    ) -> reT | tuple:
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
                return ()
