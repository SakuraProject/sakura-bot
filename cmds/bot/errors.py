# Sakura bot - Errors

import discord
from discord.ext import commands

from traceback import TracebackException, print_exc

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

    def embedding(self, description="なんらかのエラーが発生しました", title="エラー"):
        return discord.Embed(title=title, description=description, color=0xff0000)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = None

        # 振り分け
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.embedding(f"必要な引数`{error.param.name}`が足りません。")
        if isinstance(error, commands.MissingRequiredAttachment):
            embed = self.embedding(f"必要な添付ファイル引数`{error.param.name}`が足りません。")
        if isinstance(error, commands.UnexpectedQuoteError):
            embed = self.embedding(f"引用符で囲まれていない文字列の中に引用符が見つかりました: `{error.quote}`")
        if isinstance(error, commands.InvalidEndOfQuotedStringError):
            embed = self.embedding(f"引用符が閉じられた後に空白以外の文字`{error.char}`が見つかりました。")
        if isinstance(error, commands.ExpectedClosingQuoteError):
            embed = self.embedding(f"閉じる引用符`{error.char}`が見つかりませんでした。")
        if isinstance(error, commands.BadUnionArgument):
            embed = self.embedding(
                f"引数{error.param.name}が以下のすべての型に適合しませんでした。"
                f"\n{', '.join(str(t) for t in error.converters)}"
            )
        if isinstance(error, commands.BadLiteralArgument):
            embed = self.embedding(
                f"引数{error.param.name}は以下の文字列のどれかでなければいけません。"
                f"\n{', '.join(error.literals)}"
            )
        if isinstance(error, commands.PrivateMessageOnly):
            embed = self.embedding("このコマンドはDM専用です。")
        if isinstance(error, commands.NoPrivateMessage):
            embed = self.embedding("このコマンドはDMでは使用できません。")
        if isinstance(error, commands.CommandNotFound):
            embed = self.embedding(f"コマンド`{ctx.command.name}`が見つかりませんでした。")
        if isinstance(error, commands.DisabledCommand):
            embed = self.embedding("このコマンドは現在無効化されています。")
        if isinstance(error, commands.TooManyArguments):
            embed = self.embedding("コマンドに必要ない(もしくは、過剰な)引数が渡されました。")
        if isinstance(error, commands.CommandOnCooldown):
            embed = self.embedding(f"コマンドはクールダウン中です。{error.retry_after:.2f}秒お待ちください。")
        if isinstance(error, commands.MaxConcurrencyReached):
            embed = self.embedding(
                "コマンドが同時実行可能最大数に達しました。しばらく待ってから再実行してください。\n"
                f"(このコマンドは{buckets[error.per]}につき{error.number}回まで同時実行できます。)"
            )
        if isinstance(error, commands.NotOwner):
            embed = self.embedding("このコマンドはbotの所有者のみ実行できます。")
        if isinstance(error, commands.CheckFailure) and not embed:
            embed = self.embedding("なんらかの理由によりこのコマンドは使用できません。")
        if isinstance(error, commands.MessageNotFound):
            embed = self.embedding(f"指定されたメッセージ: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.MemberNotFound):
            embed = self.embedding(f"指定されたメンバー: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.GuildNotFound):
            embed = self.embedding(f"指定されたサーバー: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.UserNotFound):
            embed = self.embedding(f"指定されたユーザー: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.ChannelNotFound):
            embed = self.embedding(f"指定されたチャンネル: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.ThreadNotFound):
            embed = self.embedding(f"指定されたスレッド: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.ChannelNotReadable):
            embed = self.embedding(f"{error.argument.mention}チャンネルのメッセージ履歴を読む権限がありません。")
        if isinstance(error, commands.BadColourArgument):
            embed = self.embedding(f"指定された色: `{error.argument}`は有効な形式ではありません。")
        if isinstance(error, commands.RoleNotFound):
            embed = self.embedding(f"指定されたロール: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.BadInviteArgument):
            embed = self.embedding(f"指定された招待: `{error.argument}`が無効または期限切れです。")
        if isinstance(error, commands.EmojiNotFound):
            embed = self.embedding(f"指定された絵文字: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.PartialEmojiConversionFailure):
            embed = self.embedding(f"指定された絵文字: `{error.argument}`は有効な形式ではありません。")
        if isinstance(error, commands.GuildStickerNotFound):
            embed = self.embedding(f"指定されたスタンプ: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.ScheduledEventNotFound):
            embed = self.embedding(f"指定されたイベント: `{error.argument}`が見つかりませんでした。")
        if isinstance(error, commands.BadBoolArgument):
            embed = self.embedding(f"指定された真偽値: `{error.argument}`は有効な形式ではありません。")
        if isinstance(error, commands.RangeError):
            embed = self.embedding(
                f"指定された引数: `{error.argument}`は、範囲外です。\n"
                f"{error.minimum}以上{error.maximum}以下でなければいけません。"
            )
        if isinstance(error, commands.MissingPermissions):
            embed = self.embedding("あなたがコマンドを実行するのに必要な権限が足りません。")
            # TODO: 必要な権限を出す
        if isinstance(error, commands.BotMissingPermissions):
            embed = self.embedding("コマンドの実行に対してBotが必要な権限が足りません。")
            # TODO: 必要な権限を出す
        if isinstance(error, commands.MissingRole):
            embed = self.embedding("コマンドの実行に対してあなたが持っていなければならないロールが足りません。")
            # TODO: 必要なロールを出す
        if isinstance(error, commands.BotMissingRole):
            embed = self.embedding("コマンドの実行に対してBotが持っていなければならないロールが足りません。")
        if isinstance(error, commands.MissingAnyRole):
            embed = self.embedding("コマンドの実行に対してあなたに必要なロールを一つも持っていません。")
        if isinstance(error, commands.BotMissingAnyRole):
            embed = self.embedding("コマンドの実行に対してBotに必要なロールを一つも持っていません。")
        if isinstance(error, commands.NSFWChannelRequired):
            embed = self.embedding(f"このコマンドはNSFWチャンネル専用です。")
        if isinstance(error, commands.CommandInvokeError) and not embed:
            embed = self.embedding(
                f"なんらかのエラーが発生しました。\n`{error.original}`\n"
                "このエラーは開発者側の問題である可能性が高いです。サポートサーバーにて報告いただけると嬉しいです。"
            )
        if not embed:
            embed = self.embedding()
            channel = self.bot.get_channel(1012623774014783598)
            error_message = "".join(
                TracebackException.from_exception(error).format()
            )
            await channel.send(f"```py\n{error_message}\n```")
            embed.add_field(
                name="エラー詳細",
                value=f"```py\n{error_message if len(error_message) < 990 else error_message[:990]}\n```"
            )
        await ctx.reply(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(ErrorQuery(bot))
