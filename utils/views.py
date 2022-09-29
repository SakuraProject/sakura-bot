# Sakura Utility - Embeds View

from __future__ import annotations

from collections.abc import Sequence

from discord.ext import commands
import discord


__all__ = ("EmbedSelect", "EmbedsView", "TimeoutView")


class EmbedSelect(discord.ui.Select):
    "embed選択用のセレクトメニュー。"

    def __init__(
        self, embeds: Sequence[discord.Embed], extras: dict | None = None,
        parent: "EmbedsView" | None = None
    ):
        self.embeds = embeds
        if extras is None:
            options = [discord.SelectOption(
                label=e.title or "...", description=e.description or "...", value=str(count)
            ) for count, e in enumerate(embeds)]
        else:
            options = [discord.SelectOption(
                label=k or "...", description=extras[k] or "...", value=str(count)
            ) for count, k in enumerate(extras.keys())]
        self.parent = parent

        super().__init__(
            placeholder='見たい項目を選んでください...', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        assert interaction.message is not None
        if interaction.message.interaction:
            if interaction.message.interaction.user != interaction.user:
                return await interaction.response.send_message(
                    'あなたはこの操作をすることができません。', ephemeral=True
                )
        if not self.parent:
            pass
        elif self.parent.author_id:
            if self.parent.author_id != interaction.user:
                return await interaction.response.send_message(
                    'あなたはこの操作をすることができません。', ephemeral=True
                )
        await interaction.response.edit_message(
            embed=self.embeds[int(self.values[0])]
        )


class TimeoutView(discord.ui.View):
    """タイムアウト時に編集するビュー。

    Inspiration by: RextTeam 2022
    """

    message: discord.Message | None

    def __init__(self, children: Sequence[discord.ui.Item] | None = None):
        super().__init__()
        if children:
            for child in children:
                self.add_item(child)

    async def send(self, ctx: commands.Context, *args, **kwargs) -> discord.Message:
        "送信した後にmessageをセットします。"
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


class EmbedsView(TimeoutView):
    "Embedsビュー。初期化時にembedのリストを渡す。"

    author_id: int | None
    message: discord.Message | None
    children: list[EmbedSelect]

    def __init__(
        self, embeds: Sequence[discord.Embed],
        extras: dict[str, str] | None = None
    ):
        super().__init__()
        self.embeds = embeds
        self.message, self.author_id = None, None

        self.add_item(EmbedSelect(embeds, extras, self))

    async def send(self, ctx: commands.Context):
        "Sendして、author_idのセットもします。"
        self.author_id = ctx.author.id
        if len(self.embeds) == 1:
            msg = await ctx.send(embed=self.embeds[0])
        else:
            msg = await ctx.send(embed=self.embeds[0], view=self)
        self.message = msg
