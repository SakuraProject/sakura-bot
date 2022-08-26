# Sakura Utility - Embeds View
import discord


__all__ = ("EmbedSelect", "EmbedsView")


class EmbedSelect(discord.ui.Select):
    "embed選択用のセレクトメニュー。"

    def __init__(self, embeds: list[discord.Embed]):
        self.embeds = embeds
        options = [discord.SelectOption(
            label=e.title or "...", description=e.description or "...", value=str(count)
        ) for count, e in enumerate(embeds)]

        super().__init__(
            placeholder='見たい項目を選んでください...', min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.embeds[2].to_dict()['description'] == '(管理者専用)':
            if not ctx.author.id in self.bot.owner_ids:
                await interaction.response.edit_message("あなたは管理者ではありません。")
        await interaction.response.edit_message(embed=self.embeds[int(self.values[0])])


class EmbedsView(discord.ui.View):
    "Embedsビュー。初期化時にembedのリストを渡す。"

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()

        self.add_item(EmbedSelect(embeds))
