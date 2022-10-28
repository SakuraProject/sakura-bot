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
    "speedtest": cleandoc("""botを動かしているサーバーの速度を計測します。
        アップロード・ダウンロード速度の両方の結果が表示されます。
        このコマンドには1回実行につき1時間のクールダウンが付けられています。"""),
    "mynews": "みんなのニュース機能です。自分の投稿したいニュースを投稿できます。\n"
        "(Powered by MyNews from ysmService)",
    "mynews post": cleandoc("""みんなのニュースを投稿します。
        **使い方：**
        `sk!mynews post`
        コマンドを実行するといくつかの質問をされるのでそれに答えるだけでニュースが投稿できます。"""),
    "mynews day": cleandoc("""みんなのニュースを日付で検索します。
        **使い方：**
        `sk!mynews day 2022/10/22`"""),
    "mynews today": "今日のみんなのニュースを表示します。",
    "qr": "QRコードの生成やQRコードからの読み取りを行います。",
    "qr make": cleandoc("""テキストからQRコードを生成します。
        **使い方：**
        `sk!qr make こんにちは`
        結果としてQRコードの画像が送信されます。"""),
    "qr read": cleandoc("""QRコードを読み取ります。
        **使い方：**
        `sk!qr read` (QRコードを添付してください)"""),
    "reversi": "リバーシで遊びます。",
    "mail": cleandoc("""メールをdiscordに送信する機能です。
        **注意**
        これは実際のメールアドレス(IMAP)を使用します。
        便利な反面、情報漏洩などの恐れもあるため使用には十分ご注意ください。"""),
    "mail set": "メールを作成します。",
}
