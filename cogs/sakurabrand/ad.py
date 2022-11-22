# Sakura Ad

import random
from asyncio import TimeoutError

import discord
from discord import app_commands
from discord.ext import commands

from aiomysql import Cursor
from utils import Bot


class MakeAdModal(discord.ui.Modal):
    content = discord.ui.TextInput(
        label="広告内容", placeholder="広告の内容を入力してください。",
        style=discord.TextStyle.paragraph, required=True, max_length=2000
    )

    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        super().__init__()

    async def callback(self, interaction: discord.Interaction):
        await SakuraAd.ad_made(
            getattr(self.ctx.command, "cog"), interaction, str(self.content)
        )


class SakuraAd(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache: dict[int, dict[int, str]] = {}

    async def setup_database(self, cursor: Cursor):
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS SakuraAd(
                Id BIGINT PRIMARY KEY NOT NULL, Content TEXT,
                UserId BIGINT
            );"""
        )
        await cursor.execute("SELECT * FROM SakuraAd;")
        return await cursor.fetchall()

    async def load_cog(self):
        cache = await self.bot.execute_sql(self.setup_database)
        for ad in cache:
            self.cache.setdefault(ad[2], {})
            self.cache[ad[2]][ad[0]] = ad[1]

    def create_ad_embed(
        self, user_id: int, content: str, *, add_point: bool = False
    ) -> discord.Embed:
        "広告用のembedを生成します。"
        embed = discord.Embed(title="Sakura Ad", description=content)
        user = self.bot.get_user(user_id)
        if user:
            embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        if add_point:
            embed.set_footer(text="30ポイントを獲得しました！")
        else:
            embed.set_footer(text="悪い広告を発見したら公式サーバーまで。")
        return embed

    @commands.hybrid_group(description="自分の広告を出せる機能です。")
    async def sakura_ad(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return await ctx.send("使い方が違います。")

    @sakura_ad.command(description="広告を見ます。")
    @app_commands.rename(id_="id")
    async def view(self, ctx: commands.Context, id_: int | None = None):
        if not id_:
            user_id = random.choice(list(self.cache.keys()))
            selected_ad = random.choice(list(self.cache[user_id].keys()))
            return await ctx.send(embed=self.create_ad_embed(
                user_id, self.cache[user_id][selected_ad]
            ))
        user_ids = [k for k, v in self.cache.items() if id_ in v.keys()]
        if not user_ids:
            return await ctx.send("広告が見つかりませんでした。")
        await ctx.send(embed=self.create_ad_embed(
            user_ids[0], self.cache[user_ids[0]][id_], add_point=True
        ))
        await self.bot.cogs["SakuraPoint"].spmanage_(ctx.author, 30)

    @sakura_ad.command(description="広告を作成します。")
    async def make(self, ctx: commands.Context, content: str | None = None):
        if content:
            return await self.ad_made(ctx, content)
        if ctx.interaction:
            return await ctx.interaction.response.send_modal(MakeAdModal(ctx))
        wait_msg = await ctx.send("広告の内容を1分以内に送信してください。")
        try:
            msg = await self.bot.wait_for(
                "message", timeout=60.0,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )
        except TimeoutError:
            return await wait_msg.edit(content="タイムアウトしました。")
        else:
            return await self.ad_made(ctx, msg.content)

    async def ad_made(self, ctx: commands.Context | discord.Interaction, content: str):
        if isinstance(ctx, commands.Context):
            msg = await ctx.send("Ok")
            user_id = ctx.author.id
        else:
            if not isinstance(ctx.channel, discord.TextChannel):
                return await ctx.response.send_message("テキストチャンネルで実行し直してください。")
            msg = await ctx.channel.send("Ok")
            user_id = ctx.user.id

        await self.bot.execute_sql(
            """INSERT INTO SakuraAd VALUES (%s, %s, %s)""",
            (msg.id, content, user_id)
        )

    @sakura_ad.command(description="広告一覧を見ることができます。")
    @app_commands.describe(user_id="一覧をみたいユーザーのID")
    async def list_(self, ctx: commands.Context, user_id: int | None = None):
        user_id = user_id or ctx.author.id
        if user_id not in self.cache:
            return await ctx.send("広告がありません。")

        await ctx.send(embed=discord.Embed(
            title=f"{self.bot.get_user(user_id) or '(不明)'}の広告一覧",
            description="\n".join(
                f"`{id_}`: {content.splitlines()[0]}"
                for id_, content in self.cache[user_id].items()
            )
        ))

    @sakura_ad.command(description="広告を削除します。")
    @app_commands.rename(id_="id")
    async def delete(self, ctx: commands.Context, id_: int):
        if not any(id_ in m for m in self.cache.values()):
            return await ctx.send("広告が見つかりませんでした。")
        user_id = [k for k, v in self.cache.items() if id_ in v.keys()][0]
        if ctx.author.id != user_id:
            return await ctx.send("広告を削除する権限がありません。")
        del self.cache[user_id][id_]
        if not self.cache[user_id]:
            del self.cache[user_id]
        await self.bot.execute_sql(
            "DELETE FROM SakuraAd WHERE Id = %s;", (id_,)
        )
        await ctx.send("Ok")


async def setup(bot: Bot) -> None:
    await bot.add_cog(SakuraAd(bot))
