# Sakura bot - help data

from inspect import cleandoc


HELP = {
    "help": "このコマンドです。コマンドの使い方を確認することができます。",
    "about": "Botの情報を見ることができます。",
    "ping": cleandoc("""botの速さを調べられます。単位はms(ミリ秒)です。
        1000msを超えるようなことがあればサポートサーバーにて報告してください。"""),
    "captcha": cleandoc("""認証機能です。
        サーバーを荒らしから守るために使用できます。"""),
    "captcha web": cleandoc("""Web認証用のパネルを送信します。
        **使いかた：**
        `sk!captcha web @認証済み`
        実行すると、webサイトへのボタンを含むメッセージが送信されます。"""),
    "captcha password": cleandoc("""パスワード認証用のパネルを送信します。
        **使いかた：**
        `sk!captcha password @認証済み 開けゴマ`
        「開けゴマ」のパスワードを送信すると`@認証済み`ロールが付与されるようになります。"""),
    "userinfo": cleandoc("""ユーザー情報を表示します。
        **使いかた：**
        `sk!userinfo [ユーザー名・メンション・ID]`
        ユーザー名を省略するとあなたの情報を表示します。"""),
    "serverinfo": cleandoc("""サーバー情報を表示します。
        **使い方：**
        `sk!serverinfo [サーバー名・ID]`
        サーバー名を省略するとこのサーバーの情報を表示します。"""),
    "emojiinfo": cleandoc("""絵文字の情報を表示します。
        **使い方：**
        `sk!emojiinfo [カスタム絵文字]`
        discordにある標準絵文字には対応していませんのでご了承ください。"""),
    "inviteinfo": cleandoc("""招待リンクの情報を表示します。
        **使い方：**
        `sk!inviteinfo https://discord.gg/*********`"""),
    "say": cleandoc("""botに指定した内容を喋らせることができます。
        **使い方：**
        `sk!say hello, world!`
        everyoneやhereなどのメンションは自動的に無効化されます。"""),
    "findnewbot": cleandoc("""新しいbotを探します。
        **使い方：**
        `sk!findnewbot`
        `findnewbot`の後に`online`をつけると現在オンラインのbotのみ、
        `include_ignored`をつけると例外に設定されているbotを含めて表示します。
        例外botは主に非公開botです。
        **注意**
        例外botはデータベースを元に判定しています。
        例外botに追加してほしい・解除してほしいbotがあったらお問い合わせください。"""),
    "afk": "留守メッセージ機能です。",
    "afk set": cleandoc("""留守メッセージを設定します。
        **使い方：**
        `sk!afk set 勉強中です。`
        他の人からメンションされたときにこのbotが代わりに`勉強中です。`と送信します。"""),
    "gamesearch": cleandoc("""ゲーム機を検索します。
        **使い方：**
        `sk!gamesearch Switch`
        (Powered by ysmService Game Search Engine)"""),
    "gban": cleandoc("""グローバルBAN機能です。
        SakuraBotのデータベースに登録された人をそのサーバーに入ってきた時にBANすることができます。
        BAN権限がユーザーとBotにあることが条件です。"""),
}
