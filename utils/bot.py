# Sakura Utils - Bot

from discord.ext import commands
from aiohttp import ClientSession
from aiomysql import Pool


__all__ = ["Bot"]

class Bot(commands.Bot):
    "SakuraBotのコアです。"
    session: ClientSession
    pool: Pool

    Color = 0xffbdde

