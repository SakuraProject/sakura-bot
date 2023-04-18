# Sakura Utils - Bot

from typing import TypeVar, Any, Callable, Literal, overload
from collections.abc import Coroutine

from inspect import iscoroutinefunction

import discord
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
    user: discord.ClientUser
    cogs: Cogs
    user_prefixes: dict[int, str]
    guild_prefixes: dict[int, str]
    voice_clients: list[discord.VoiceClient]

    Color = 0xffbdde

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("command_prefix", self._get_prefix)
        super().__init__(*args, **kwargs)
        self._session = None
        self.user_prefixes = {}
        self.guild_prefixes = {}
        self.load_private_module()

    def load_private_module(self):
        "プライベートモジュールの読み込みをします。"
        import importlib
        try:
            self.private = importlib.import_module("sakura_private")
        except:
            from . import private_dummy
            self.private = private_dummy

    @property
    def session(self) -> ClientSession:
        if not self._session or self._session.closed:
            self._session = ClientSession(loop=self.loop, json_serialize=loads)
        return self._session

    def _get_prefix(self, _, message: discord.Message):
        prefixes = ["sk!", "Sk!", "SK!", "sk! ", "sk !", "sk！", "sk ! "]
        if message.guild and message.guild.id in self.guild_prefixes:
            prefixes.append(self.guild_prefixes[message.guild.id])
        if message.author.id in self.user_prefixes:
            prefixes.append(self.user_prefixes[message.author.id])
        return prefixes

    @overload
    async def execute_sql(
        self, sql: str, _injects: tuple | None = None,
        _return_type: Literal[""] = ...
    ) -> tuple | None:
        ...
    @overload
    async def execute_sql(
        self, sql: str, _injects: tuple | None = None,
        _return_type: Literal["fetchone"] = ...
    ) -> tuple[Any, ...]:
        ...
    @overload
    async def execute_sql(
        self, sql: str, _injects: tuple | None = None,
        _return_type: Literal["fetchall"] = ...
    ) -> tuple[tuple, ...]:
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
    ) -> reT | tuple | None:
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
