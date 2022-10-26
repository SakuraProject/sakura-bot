# Sakura Bot - Role Linker

from typing import Literal

from orjson import loads

from discord.ext import commands
from discord import app_commands
import discord

from utils import Bot, dumps


class RoleLinkEthicsError(Exception):
    "ロールリンカーでループが確認された時に出るエラー。"

    def __init__(self, groups: list[str]):
        self.groups = groups
        super().__init__("リンカーグループのループが確認されました。")


class RoleLinker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache: dict[int, dict[
            str, tuple[Literal["sync", "antisync"], list[int]]]] = {}

    def ethics_checker(self, guild_id: int):
        "ロールリンカーの倫理違反をチェックします。"
        g_cache = self.cache[guild_id]
        for group_name in g_cache.keys():
            # 現在のロールを適当にいれてみる。
            group_data = g_cache[group_name][1]
            self.ethics_checker_test_event(
                guild_id, [group_name], group_data, group_data[0]
            )

    def ethics_checker_test_event(
        self, guild_id: int, groups: list[str],
        now_roles: list[int], role: int
    ):
        g_cache = self.cache[guild_id]
        for name, group in g_cache.items():
            if role not in group[1]:
                continue
            if group[0] == "sync":
                # 同期させる。
                if name in groups:
                    raise ValueError("倫理違反")
                for _role in group[1]:
                    if _role not in now_roles:
                        # リストに追加して再度呼び出し
                        groups.append(name)
                        now_roles.append(_role)
                        self.ethics_checker_test_event(guild_id, groups, now_roles, _role)
            else:
                # 逆同期させる。
                if name in groups:
                    raise ValueError("倫理違反")
                for _role in group[1]:
                    if _role in now_roles:
                        raise ValueError("倫理違反")

    async def cog_load(self):
        await self.bot.execute_sql(
            """CREATE TABLE IF NOT EXISTS RoleLinker(
                GuildId BIGINT NOT NULL, Name VARCHAR(16) DEFAULT 'main',
                Mode Enum('sync', 'antisync'), Roles JSON
            ) PRIMARY KEY(GuildId, Name);"""
        )
        cache = await self.bot.execute_sql(
            "SELECT * FROM RoleLinker;", _return_type="fetchall"
        )
        for guild_id, name, mode, roles_raw in cache:
            if guild_id not in self.cache:
                self.cache[guild_id] = {name: (mode, loads(roles_raw))}
            self.cache[guild_id][name] = (mode, loads(roles_raw))

    @commands.hybrid_group(description="ロールリンカー機能です。", fallback="view")
    @commands.guild_only()
    async def role_linker(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        assert ctx.guild
        if ctx.guild.id not in self.cache or not self.cache[ctx.guild.id]:
            return await ctx.send("ロールリンカーをまだなにも登録していません。")

        linkers = self.cache[ctx.guild.id]
        embed = discord.Embed(title="ロールリンカー一覧")
        for linker in linkers.keys():
            embed.add_field(
                name=linker,
                value=f"モード: {'同期' if linkers[linker][0] == 'sync' else '逆同期'}\nロール: "
                      + ", ".join(
                        getattr(ctx.guild.get_role(int(role)), "mention", "不明なロール")
                        for role in linkers[linker][1]))
        await ctx.send(embed=embed)

    @role_linker.command("set", description="ロールリンカーを設定します。")
    @app_commands.describe(
        name="リンクグループ名", mode="同期か逆同期か", roles="リンクするロール"
    )
    async def _set(
        self, ctx: commands.Context, name: str, mode: Literal["sync", "antisync"],
        roles: commands.Greedy[discord.Role]
    ):
        assert ctx.guild
        try:
            self.ethics_checker(ctx.guild.id)
        except RoleLinkEthicsError as e:
            return await ctx.send(embed=discord.Embed(
                title="ロール付与ループが発生するため、このグループは登録できません。",
                description="→".join(e.groups[e.groups.index(e.groups[-1]):])
            ))
        if ctx.guild.id not in self.cache:
            self.cache[ctx.guild.id] = {}
        self.cache[ctx.guild.id][name] = (mode, [r.id for r in roles])

        await self.bot.execute_sql(
            "INSERT INTO RoleLinker VALUES(%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE Mode=VALUE(Mode), Roles=VALUE(Roles)",
            (ctx.guild.id, name, mode, dumps(roles))
        )
        await ctx.reply("Ok")

    @role_linker.command(description="ロールリンカーを削除します。")
    @app_commands.describe(name="リンクグループ名")
    async def delete(self, ctx, name: str):
        assert ctx.guild
        if ctx.guild.id not in self.cache or name not in self.cache[ctx.guild.id]:
            return await ctx.send("その名前のリンクグループは登録されていません！")
        del self.cache[ctx.guild.id][name]
        await self.bot.execute_sql(
            "DELETE FROM RoleLinker WHERE GuildId = %s AND Name = %s",
            (ctx.guild.id, name,)
        )
        await ctx.reply("Ok")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return
        if before.guild.id not in self.cache or not self.cache[before.guild.id]:
            return
        # 付与・削除の検知
        for role in after.roles:
            if not (role.is_default() or before.get_role(role.id)):
                await self.role_add(before, role)
        for role in before.roles:
            if not (role.is_default() or after.get_role(role.id)):
                await self.role_remove(after, role)

    async def role_add(self, before: discord.Member, role: discord.Role):
        for group_name in self.cache[before.guild.id].keys():
            group = self.cache[before.guild.id][group_name]
            if role.id not in group[1]:
                continue
            if group[0] == "sync":
                roles = [r for r in group[1]
                         if r != role.id and before.guild.get_role(r)
                         and not before.get_role(r)]
                try:
                    await before.add_roles(
                        *(discord.Object(r) for r in roles),
                        reason="Sakura Bot Role Linker"
                    )
                except discord.Forbidden | discord.HTTPException:
                    pass
            else:
                roles = [r for r in group[1]
                         if r != role.id and before.guild.get_role(r)
                         and before.get_role(r)]
                try:
                    await before.remove_roles(
                        *(discord.Object(r) for r in roles),
                        reason="Sakura bot Role Linker"
                    )
                except discord.Forbidden | discord.HTTPException:
                    pass

    async def role_remove(self, after: discord.Member, role: discord.Role):
        for group_name in self.cache[after.guild.id].keys():
            group = self.cache[after.guild.id][group_name]
            if role.id not in group[1]:
                continue

            if group[0] == "sync":
                roles = [r for r in group[1]
                         if r != role.id and after.guild.get_role(r)
                         and after.get_role(r)]
                try:
                    await after.remove_roles(
                        *(discord.Object(_role) for _role in roles),
                        reason="Sakura Bot Role Linker"
                    )
                except discord.Forbidden | discord.HTTPException:
                    pass
            else:
                if len(group[1]) != 2:
                    # グループのロールが2つの時のみもう片方を付与する。
                    continue
                try:
                    group[1].remove(role.id)
                    await after.add_roles(
                        discord.Object(group[1][0]),
                        reason="Sakura Bot Role Linker"
                    )
                except discord.Forbidden | discord.HTTPException:
                    pass


async def setup(bot: Bot) -> None:
    await bot.add_cog(RoleLinker(bot))
