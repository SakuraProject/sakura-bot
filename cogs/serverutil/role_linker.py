# Sakura Bot - Role Linker

from orjson import loads

from discord.ext import commands

from utils import Bot


class RoleLinker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache = {}

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS RoleLinker(
                GuildId BIGINT NOT NULL, NAME VARCHAR(16) DEFAULT 'main',
                Roles JSON
            );"""
        )
        cache = await self.bot.execute_sql(
            "SELECT * FROM RoleLinker;", _return_type="fetchall"
        )
        for guild_id, name, roles_raw in cache:
            if guild_id not in self.cache:
                self.cache[guild_id] = {name: loads(roles_raw)}
            self.cache[guild_id][name] = loads(roles_raw)


async def setup(bot: Bot) -> None:
    await bot.add_cog(RoleLinker(bot))
