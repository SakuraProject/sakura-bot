# Sakura Utility - Embeds View

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TYPE_CHECKING

from discord.ext import commands
import discord

if TYPE_CHECKING:
    from .bot import Bot


class EmbedSelect(discord.ui.Select):
    "embed選択用のセレクトメニュー。"

    view: "MyView" | None

    def __init__(
        self, embeds: Sequence[discord.Embed], extras: dict = {},
    ):
        self.embeds = embeds
        options = []
        for count, embed in enumerate(embeds):
            options.append(discord.SelectOption(
                label=embed.title or "...",
                description=(extras.get(embed.title) or embed.description or "...")[:100],
                value=str(count)
            ))

        super().__init__(
            placeholder='見たい項目を選んでください...', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.view and self.view.author_id:
            if self.view.author_id != interaction.user.id:
                return await interaction.response.send_message(
                    'あなたはこの操作をすることができません。', ephemeral=True
                )
        await interaction.response.edit_message(
            embed=self.embeds[int(self.values[0])]
        )


class MyView(discord.ui.View):
    """タイムアウト時に編集をしたり、ユーザーが操作できるかを自動で調べるビュー。
    使い方:
      await MyView([Selects, Buttons, ...]).send(ctx, 'Select from bottom...')

    class Selects(discord.ui.Select):
      view: MyView | None

      async def callback(self, interaction):
        if self.view and self.view.check(interaction):
          # この時点で操作できない場合は操作できないという返信がされている
          return
    """

    message: discord.Message | None = None
    author_id: int | None = None

    def __init__(self, children: Sequence[discord.ui.Item] | None = None):
        super().__init__()
        if children:
            for child in children:
                self.add_item(child)

    async def check(self, interaction: discord.Interaction) -> bool:
        "ユーザーが操作できないかどうか調べます。"
        if self.author_id and self.author_id != interaction.user.id:
            await interaction.response.send_message(
                'あなたはこの操作をすることができません。', ephemeral=True
            )
            return True
        elif self.message and self.message.author != interaction.user:
            await interaction.response.send_message(
                'あなたはこの操作をすることができません。', ephemeral=True
            )
            return True
        return False

    async def send(self, ctx: commands.Context, *args, **kwargs) -> discord.Message:
        "送信した後にmessageをセットします。引数にviewを含める必要はありません。"
        kwargs.setdefault("view", self)
        self.author_id = ctx.author.id
        message = await ctx.send(*args, **kwargs)
        self.message = message
        return message

    async def on_timeout(self):
        if not self.message:
            return
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True  # type: ignore
        await self.message.edit(view=self)

    async def on_error(
        self, interaction: discord.Interaction, error: commands.CommandError,
        item: discord.ui.Item[Any], /
    ) -> None:
        if isinstance(interaction.client, Bot):
            try:
                ctx = await commands.Context.from_interaction(interaction)  # type: ignore
                await interaction.client.cogs["ErrorQuery"].on_command_error(ctx, error)
            except ValueError:
                pass
        return await super().on_error(interaction, error, item)


class EmbedsView(MyView):
    "Embedsビュー。初期化時にembedのリストを渡す。"

    children: list[EmbedSelect]

    def __init__(
        self, embeds: Sequence[discord.Embed],
        extras: dict[str, str] = {}
    ):
        super().__init__()
        self.embeds = embeds
        self.message, self.author_id = None, None

        self.add_item(EmbedSelect(embeds, extras))

    async def send(self, ctx: commands.Context, *args, **kwargs):
        "Sendします。"
        if "embed" in kwargs or "embeds" in kwargs:
            raise KeyError("No Embed key-word arguments are arrowed.")
        if len(self.embeds) == 1:
            return await super().send(ctx, *args, embed=self.embeds[0], **kwargs)
        else:
            view = kwargs.pop("view") or self
            return await super().send(
                ctx, *args, embed=self.embeds[0], view=view, **kwargs
            )


class EmbedsButtonView(MyView):
    "Embedsビューのボタンバージョン。"

    def __init__(self, embeds: Sequence[discord.Embed]):
        self.embeds = embeds
        self.page = 0
        super().__init__()

    @discord.ui.button(label="<")
    async def left(self, interaction: discord.Interaction, _):
        if self.check(interaction):
            return
        if self.page != 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
        else:
            return await interaction.response.send_message("このページが最初です", ephemeral=True)

    @discord.ui.button(label=">")
    async def right(self, interaction: discord.Interaction, _):
        if self.check(interaction):
            return
        if self.page != len(self.embeds) - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
        else:
            return await interaction.response.send_message("次のページはありません", ephemeral=True)

    async def send(self, ctx: commands.Context, *args, **kwargs):
        "Sendします。"
        if len(self.embeds) == 1:
            return await super().send(ctx, embed=self.embeds[0])
        else:
            return await super().send(ctx, embed=self.embeds[0], view=self)
