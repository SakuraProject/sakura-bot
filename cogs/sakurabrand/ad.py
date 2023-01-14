# Sakura Ad

from collections.abc import Coroutine, Callable

import random
from asyncio import TimeoutError

import discord
from discord import app_commands
from discord.ext import commands

from aiomysql import Cursor
from utils import Bot


# Monkey Patch
# SakuraAdを自動で表示するためのモンキーパッチ。

def auto_send_wrapper(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
    async def sender(self, *args, **kwargs):
        if kwargs.get("embed"):
            bot = self._state._get_client()
            if isinstance(bot, Bot) and random.random() > 0.7 and (
                self.author.id not in bot.cogs["SakuraAd"].invisible_cache
            ):
                ad_data = bot.cogs["SakuraAd"].get_random_ad_embed()
                kwargs["embeds"] = [kwargs.pop("embed"), ad_data]
        return await func(self, *args, **kwargs)
    return sender

commands.Context.send = auto_send_wrapper(commands.Context.send)


class MakeAdModal(discord.ui.Modal):
    content = discord.ui.TextInput(
        label="広告内容", placeholder="広告の内容を入力してください。",
        style=discord.TextStyle.paragraph, required=True, max_length=2000
    )

    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        super().__init__()

    async def callback(self, interaction: discord.Interaction) -> None:
        await SakuraAd.ad_made(
            getattr(self.ctx.command, "cog"), interaction, str(self.content)
        )


class SakuraAd(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cache: dict[int, dict[int, str]] = {}
        self.invisible_cache: list[int] = []

    async def setup_database(self, cursor: Cursor) -> tuple[
        tuple[tuple[int, str, int], ...], tuple[tuple[int], ...]
    ]:
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS SakuraAd(
                Id BIGINT PRIMARY KEY NOT NULL, Content TEXT,
                UserId BIGINT
            );"""
        )
        await cursor.execute("SELECT * FROM SakuraAd;")
        cache1 = await cursor.fetchall()
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS SakuraAdInvisible(
                Id BIGINT PRIMARY KEY NOT NULL
            );"""
        )
        await cursor.execute("SELECT * FROM SakuraAdInvisible;")
        return (cache1, await cursor.fetchall())

    async def load_cog(self) -> None:
        cache1, cache2 = await self.bot.execute_sql(self.setup_database)
        for ad in cache1:
            self.cache.setdefault(ad[2], {})
            self.cache[ad[2]][ad[0]] = ad[1]
        self.invisible_cache = [row[0] for row in cache2]

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

    def get_random_ad_embed(self) -> discord.Embed:
        choices = list(self.cache.keys())
        choices.append(0)
        user_id = random.choice(choices)
        if user_id == 0:
            return self.create_ad_embed(
                self.bot.user.id, "SakuraBotの導入よろしくお願いします！\n"
                "[導入する](https://discord.com/api/oauth2/authorize?client_id=985852917489737728&permissions=8&scope=applications.commands%20bot)"
                "\n[公式サーバーに参加](https://discord.gg/KW4CZvYMJg/)\n"
                "[公式サイト](https://sakura-bot.net/)"
            )
        selected_ad = random.choice(list(self.cache[user_id].keys()))
        return self.create_ad_embed(
            user_id, self.cache[user_id][selected_ad]
        )

    @sakura_ad.command(description="広告を見ます。")
    @app_commands.rename(id_="id")
    async def view(self, ctx: commands.Context, id_: int | None = None):
        if not id_:
            return await ctx.send(embed=self.get_random_ad_embed())

        user_ids = [k for k, v in self.cache.items() if id_ in v.keys()]
        if not user_ids:
            return await ctx.send("広告が見つかりませんでした。")

        await ctx.send(embed=self.create_ad_embed(
            user_ids[0], self.cache[user_ids[0]][id_], add_point=True
        ))
        await self.bot.cogs["SakuraPoint"].spmanage_(ctx.author, 30)

    @sakura_ad.command(description="広告を作成します。")
    async def make(self, ctx: commands.Context, content: str | None = None):
        if not self.bot.cogs["SakuraPoint"].spcheck(ctx.author.id):
            return await ctx.send("あなたはSakuraPointを持っていない(もしくは、0以下)です！")

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

    async def ad_made(self, ctx: commands.Context | discord.Interaction, content: str) -> None:
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
                f"`{id_}`: {len(content)}文字 ({100+int(len(content)*0.7)}ポイント消費)"
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

    @sakura_ad.command(description="広告非表示のオンオフをします。")
    async def invisible(self, ctx: commands.Context):
        now = ctx.author.id in self.invisible_cache
        if now:
            await self.bot.execute_sql(
                "DELETE FROM SakuraAdInvisible WHERE UserId = %s;", (ctx.author.id,)
            )
            self.invisible_cache.remove(ctx.author.id)
        else:
            if self.bot.cogs["SakuraPoint"].spcheck(ctx.author.id):
                return await ctx.send(
                    "あなたはSakuraPointを持っていない(または0以下)のためオンにできません。"
                )
            await self.bot.execute_sql(
                "INSERT INTO SakuraAdInvisible VALUES (%s);", (ctx.author.id,)
            )
            self.invisible_cache.append(ctx.author.id)
        await ctx.send(f"広告非表示を{'オフ' if now else 'オン'}にしました。")


async def setup(bot: Bot) -> None:
    await bot.add_cog(SakuraAd(bot))
