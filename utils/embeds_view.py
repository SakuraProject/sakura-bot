# Sakura Utility - Embeds View

from collections.abc import Sequence

from discord.ext import commands
import discord


__all__ = ("EmbedSelect", "EmbedsView")


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
        elif self.parent.message:
            if self.parent.message.author != interaction.user:
                return await interaction.response.send_message(
                    'あなたはこの操作をすることができません。', ephemeral=True
                )
        elif self.parent.author_id:
            if self.parent.author_id != interaction.user:
                return await interaction.response.send_message(
                    'あなたはこの操作をすることができません。', ephemeral=True
                )
        await interaction.response.edit_message(
            embed=self.embeds[int(self.values[0])]
        )


class EmbedsView(discord.ui.View):
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

        self.add_item(EmbedSelect(embeds, extras))

    async def send(self, ctx: commands.Context):
        "Sendして、author_idのセットもします。"
        self.author_id = ctx.author.id
        if len(self.embeds) == 1:
            msg = await ctx.send(embed=self.embeds[0])
        else:
            msg = await ctx.send(embed=self.embeds[0], view=self)
        self.message = msg

    async def on_timeout(self):
        if not self.message:
            return
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
