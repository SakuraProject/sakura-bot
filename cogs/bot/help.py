from __future__ import annotations

import os
import inspect

import discord
from discord.ext import commands

from utils import Bot, TimeoutView
from data.help import HELP


FIRST_DESC = ("これはBotのヘルプです。下の選択メニューからカテゴリを選ぶことによりコマンドを選択できます。"
              "これを見てもよくわからない方はサポートサーバーまでお問い合わせください。")


class Help(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command(
        description="ヘルプを表示します。", aliases=["ヘルプ"]
    )
    async def help(self, ctx: commands.Context, *, search_query: str | None = None):
        embed = self.create_help(search_query)
        view = TimeoutView([CategoryList(self)])
        await view.send(ctx, embed=embed, view=view)

    def create_help(self, query: str | None, _mode: bool | None = None) -> discord.Embed:
        "helpのEmbedを生成します。"
        embed = discord.Embed(color=self.bot.Color, description=FIRST_DESC)
        if query:
            # ヘルプを検索する。
            # TODO: help全文からレーベンシュタイン距離による検索をする。
            if parfect := HELP.get(query):
                if _mode:
                    for k, v in self.get_sub_commands(query).items():
                        embed.add_field(name=k, value=v)
                embed.description = parfect
            else:
                embed.description = "そのコマンドは見つかりませんでした。"
        return embed

    def get_sub_commands(self, cmd_name: str) -> dict[str, str]:
        "サブコマンド一覧を返します。"
        return {k: v for k, v in HELP.items() if k.split()[0] == cmd_name}

    def get_category(self, command: commands.Command) -> str:
        "コマンドからカテゴリ名を取得します。"
        paths = inspect.getfile(command.callback).split(os.path.sep)
        if "cogs" not in paths:
            return "others"
        category_name = paths[paths.index("cogs") - len(paths) + 1]
        return category_name

    def get_categories(self) -> list[str]:
        "カテゴリ名のリストを取得します。"
        return list(self.create_categories_commands().keys())

    def create_categories_commands(self) -> dict[str, list[str]]:
        "カテゴリとコマンドを入れ子にしたデータを取得できます。"
        result = {}
        for cmd_name in HELP.keys():
            command = self.bot.get_command(cmd_name)
            if not command:
                continue
            category = self.get_category(command)
            if category not in result:
                result[category] = [cmd_name]
            else:
                result[category].append(cmd_name)
        return result

    def convert_commands(self, cmds: list[str]) -> list[commands.Command]:
        "コマンド名のリストからコマンドのリストに変換します。"
        result = []
        for cmd_name in cmds:
            cmd = self.bot.get_command(cmd_name)
            if not cmd:
                continue
            result.append(cmd)
        return result


class CategoryList(discord.ui.Select):
    def __init__(self, cog: Help):
        self.cog = cog

        options = []
        for category_name in self.cog.get_categories():
            options.append(discord.SelectOption(
                label=category_name, value=category_name
            ))
        super().__init__(
            placeholder='カテゴリを選択...', min_values=1,
            max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # コマンド一覧を生成する
        desc = ""
        for cmd_name in self.cog.create_categories_commands()[self.values[0]]:
            if " " in cmd_name:
                # サブコマンドは一覧に表示しない
                continue
            cmd = self.cog.bot.get_command(cmd_name)
            assert cmd
            if cmd.description:
                desc += f"\n{cmd_name}: {cmd.description}"
            else:
                desc += f"\n{cmd_name}: {HELP[cmd_name].splitlines()[0]}"
        embed = discord.Embed(title=self.values[0], description=desc)
        view = TimeoutView([self, CmdList(self.values[0], self.cog)])
        view.message = interaction.message
        await interaction.response.edit_message(embeds=[embed], view=view)


class CmdList(discord.ui.Select):
    def __init__(self, category_name: str, cog: Help):
        self.cog = cog
        options = []
        self.category_name = category_name
        self.cmds = cog.convert_commands(
            [c for c in cog.create_categories_commands()[category_name] if " " not in c]
        )
        for cm in self.cmds:
            options.append(discord.SelectOption(
                label=cm.qualified_name, value=cm.qualified_name
            ))
        super().__init__(
            placeholder='コマンドを選択...', min_values=1,
            max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        bot = self.cog.bot
        val = self.values[0]
        cmd = bot.get_command(val)
        embed = self.cog.create_help(val)
        if isinstance(cmd, commands.Command | commands.HybridCommand):
            await interaction.response.edit_message(embeds=[embed])
        else:
            view = TimeoutView(
                [CategoryList(self.cog), CmdList(self.category_name, self.cog)]
            )
            await interaction.response.edit_message(embeds=[embed], view=view)
            view.message = interaction.message


async def setup(bot: Bot):
    await bot.add_cog(Help(bot))
