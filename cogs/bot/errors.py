# Sakura bot - Errors

import discord
from discord.ext import commands

from traceback import TracebackException

from utils import Bot


buckets = {
    commands.BucketType.default: "全サーバー",
    commands.BucketType.user: "1ユーザー",
    commands.BucketType.guild: "1サーバー",
    commands.BucketType.channel: "1チャンネル",
    commands.BucketType.member: "1メンバー",
    commands.BucketType.category: "1カテゴリ",
    commands.BucketType.role: "1ロール",
}


class ErrorQuery(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="エラー", description="", color=0xff0000)

        # 振り分け
        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"必要な引数`{error.param.name}`が足りません。"
        if isinstance(error, commands.MissingRequiredAttachment):
            embed.description = f"必要な添付ファイル引数`{error.param.name}`が足りません。"
        if isinstance(error, commands.UnexpectedQuoteError):
            embed.description = f"引用符で囲まれていない文字列の中に引用符が見つかりました: `{error.quote}`"
        if isinstance(error, commands.InvalidEndOfQuotedStringError):
            embed.description = f"引用符が閉じられた後に空白以外の文字`{error.char}`が見つかりました。"
        if isinstance(error, commands.ExpectedClosingQuoteError):
            embed.description = f"閉じる引用符`{error.close_quote}`が見つかりませんでした。"
        if isinstance(error, commands.BadUnionArgument):
            embed.description = (f"引数{error.param.name}が以下のすべての型に適合しませんでした。"
                                 f"\n{', '.join(str(t) for t in error.converters)}")
        if isinstance(error, commands.BadLiteralArgument):
            embed.description = (f"引数{error.param.name}は以下の文字列のどれかでなければいけません。"
                                 f"\n{', '.join(error.literals)}")
        if isinstance(error, commands.PrivateMessageOnly):
            embed.description = "このコマンドはDM専用です。"
        if isinstance(error, commands.NoPrivateMessage):
            embed.description = "このコマンドはDMでは使用できません。"
        if isinstance(error, commands.CommandNotFound):
            embed.description = "そのコマンドが見つかりませんでした。"
        if isinstance(error, commands.DisabledCommand):
            embed.description = "このコマンドは現在無効化されています。"
        if isinstance(error, commands.TooManyArguments):
            embed.description = "コマンドに必要ない(もしくは、過剰な)引数が渡されました。"
        if isinstance(error, commands.CommandOnCooldown):
            embed.description = f"コマンドはクールダウン中です。{error.retry_after:.2f}秒お待ちください。"
        if isinstance(error, commands.MaxConcurrencyReached):
            embed.description = (
                "コマンドが同時実行可能最大数に達しました。しばらく待ってから再実行してください。\n"
                f"(このコマンドは{buckets[error.per]}につき{error.number}回まで同時実行できます。)"
            )
        if isinstance(error, commands.NotOwner):
            embed.description = "このコマンドはbotの所有者のみ実行できます。"
        if isinstance(error, commands.CheckFailure) and not embed:
            embed.description = "なんらかの理由によりこのコマンドは使用できません。"
        if isinstance(error, commands.MessageNotFound):
            embed.description = f"指定されたメッセージ: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.MemberNotFound):
            embed.description = f"指定されたメンバー: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.GuildNotFound):
            embed.description = f"指定されたサーバー: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.UserNotFound):
            embed.description = f"指定されたユーザー: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.ChannelNotFound):
            embed.description = f"指定されたチャンネル: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.ThreadNotFound):
            embed.description = f"指定されたスレッド: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.ChannelNotReadable):
            embed.description = f"{error.argument.mention}チャンネルのメッセージ履歴を読む権限がありません。"
        if isinstance(error, commands.BadColourArgument):
            embed.description = f"指定された色: `{error.argument}`は有効な形式ではありません。"
        if isinstance(error, commands.RoleNotFound):
            embed.description = f"指定されたロール: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.BadInviteArgument):
            embed.description = f"指定された招待: `{error.argument}`が無効または期限切れです。"
        if isinstance(error, commands.EmojiNotFound):
            embed.description = f"指定された絵文字: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.PartialEmojiConversionFailure):
            embed.description = f"指定された絵文字: `{error.argument}`は有効な形式ではありません。"
        if isinstance(error, commands.GuildStickerNotFound):
            embed.description = f"指定されたスタンプ: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.ScheduledEventNotFound):
            embed.description = f"指定されたイベント: `{error.argument}`が見つかりませんでした。"
        if isinstance(error, commands.BadBoolArgument):
            embed.description = f"指定された真偽値: `{error.argument}`は有効な形式ではありません。"
        if isinstance(error, commands.RangeError):
            embed.description = (
                f"指定された引数: `{error.value}`は、範囲外です。\n"
                f"{error.minimum}以上{error.maximum}以下でなければいけません。"
            )
        if isinstance(error, commands.MissingPermissions):
            embed.description = "あなたがコマンドを実行するのに必要な権限が足りません。"
            # TODO: 必要な権限を出す
        if isinstance(error, commands.BotMissingPermissions):
            embed.description = "コマンドの実行に対してBotが必要な権限が足りません。"
            # TODO: 必要な権限を出す
        if isinstance(error, commands.MissingRole):
            embed.description = "コマンドの実行に対してあなたが持っていなければならないロールが足りません。"
            # TODO: 必要なロールを出す
        if isinstance(error, commands.BotMissingRole):
            embed.description = "コマンドの実行に対してBotが持っていなければならないロールが足りません。"
        if isinstance(error, commands.MissingAnyRole):
            embed.description = "コマンドの実行に対してあなたに必要なロールを一つも持っていません。"
        if isinstance(error, commands.BotMissingAnyRole):
            embed.description = "コマンドの実行に対してBotに必要なロールを一つも持っていません。"
        if isinstance(error, commands.NSFWChannelRequired):
            embed.description = "このコマンドはNSFWチャンネル専用です。"
        if not embed.description:
            embed.description = (
                f"なんらかのエラーが発生しました。\n`{error}`\n"
                "このエラーは開発者側の問題である可能性が高いです。サポートサーバーにて報告いただけると嬉しいです。"
            )
            channel = self.bot.get_channel(1012623774014783598)

            assert isinstance(channel, discord.TextChannel)
            error_message = "".join(
                TracebackException.from_exception(error).format()
            )

            print("\033[31m" + error_message + "\033[0m")

            await channel.send(
                f"""発生サーバー：{getattr(ctx.guild, 'name')}(ID:{getattr(ctx.guild, 'id')})
                    発生チャンネル：{getattr(ctx.channel, "name")}(ID:{ctx.channel.id})
                    発生ユーザー：{ctx.author}(ID:{ctx.author.id})
                    発生コマンド：{getattr(ctx.command, "name")}(`{ctx.message.content}`)""",
                embed=discord.Embed(
                    title="エラー詳細", description=f"```py\n{error_message}\n```")
            )

            embed.add_field(
                name="エラー詳細",
                value=f"```py\n{error_message if len(error_message) < 990 else error_message[:990] + '...'}\n```"
            )

        await ctx.reply(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(ErrorQuery(bot))
