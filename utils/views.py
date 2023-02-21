# Sakura Utility - Embeds View

from __future__ import annotations

from collections.abc import Sequence

from discord.ext import commands
import discord


class EmbedSelect(discord.ui.Select):
    "embed選択用のセレクトメニュー。"

    view: "MyView" | None

    def __init__(
        self, embeds: Sequence[discord.Embed], extras: dict | None = None,
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
    "タイムアウト時に編集をしたり、ユーザーが操作できるかを自動で調べるビュー。"

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


class EmbedsView(MyView):
    "Embedsビュー。初期化時にembedのリストを渡す。"

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
        "Sendします。"
        if len(self.embeds) == 1:
            await super().send(ctx, embed=self.embeds[0])
        else:
            await super().send(ctx, embed=self.embeds[0], view=self)


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

    async def send(self, ctx: commands.Context):
        "Sendします。"
        if len(self.embeds) == 1:
            await super().send(ctx, embed=self.embeds[0])
        else:
            await super().send(ctx, embed=self.embeds[0], view=self)
