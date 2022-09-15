# Sakura Utility - Embeds View

from collections.abc import Sequence

from discord.ext import commands
import discord


__all__ = ("EmbedSelect", "EmbedsView")


class EmbedSelect(discord.ui.Select):
    "embed選択用のセレクトメニュー。"

    def __init__(self, embeds: Sequence[discord.Embed], extras: dict | None = None):
        self.embeds = embeds
        if extras is None:
            options = [discord.SelectOption(
                label=e.title or "...", description=e.description or "...", value=str(count)
            ) for count, e in enumerate(embeds)]
        else:
            options = [discord.SelectOption(
                label=k or "...", description=extras[k] or "...", value=str(count)
            ) for count, k in enumerate(extras.keys())]

        super().__init__(
            placeholder='見たい項目を選んでください...', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        assert interaction.message is not None
        assert interaction.message.interaction is not None
        if interaction.message.interaction.user != interaction.user:
            return await interaction.response.send_message(
                'あなたはこの操作をすることができません。', ephemeral=True
            )
        await interaction.response.edit_message(embed=self.embeds[int(self.values[0])])


class EmbedsView(discord.ui.View):
    "Embedsビュー。初期化時にembedのリストを渡す。"

    def __init__(
        self, embeds: Sequence[discord.Embed],
        extras: dict[str, str] | None = None
    ):
        super().__init__()
        self.embeds = embeds

        self.add_item(EmbedSelect(embeds, extras))

    async def send(self, ctx: commands.Context):
        if len(self.embeds) == 1:
            await ctx.send(embed=self.embeds[0])
        else:
            await ctx.send(embed=self.embeds[0], view=self)
