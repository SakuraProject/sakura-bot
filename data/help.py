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
    "mail set": "メール通知を設定します。",
    "mail remove": "メール通知を解除します。",
    "online_notice": "オンライン通知機能です。",
    "online_notice add": cleandoc("""オンライン通知を設定します。
        **使い方：**
        `sk!online_notice add @test-user`
        @test-user がオンラインになったときに通知します。"""),
    "online_notice remove": cleandoc("""オンライン通知を解除します。
        **使い方：**
        `sk!online_notice remove @test-user`
        @test-userがオンラインになっても通知しなくなります。"""),
    "spoint": "自分の持っているSakuraPointを確認できます。",
    "schedule": "スケジュール機能です。",
    "schedule set": cleandoc("""スケジュールを設定します。
        **使い方：**
        `sk!schedule set [開始時刻] [終了時刻] [日付] [DM通知するかどうか] [タイトル]`
        `sk!schedule set 06:00 12:00 2023/01/01 True 元旦`
        開始・終了の時刻、日付は0埋めをしてください。"""),
    "schedule delete": cleandoc("""スケジュールを削除します。
        **使い方：**
        `sk!schedule delete 元旦`"""),
    "schedule list": "スケジュール一覧を表示します。",
    "tweet": "ツイッター通知機能です。",
    "tweet set": cleandoc("""ツイッター通知を設定します。
        **使い方：**
        `sk!tweet set yaakiyu`
        (ちなみにyaakiyuは開発者の一人です。ほぼツイートしないけど。)"""),
    "tweet remove": cleandoc("""ツイッター通知を削除します。
        **使い方：**
        `sk!tweet remove yaakiyu`"""),
    "bumponoff": cleandoc("""DISBOARDのBump通知を設定します。
        **使い方：**
        `sk!bumponoff on @bump通知`
        bump通知というロールにメンションするようになります。
        ロールは省略可能です。"""),
    "tossonoff": cleandoc("""glow-botのtoss通知を設定します。
        **使い方：**
        `sk!tossonoff on @toss通知`
        toss通知というロールにメンションするようになります。
        ロールは省略可能です。"""),
    "uponoff": cleandoc("""ディス速のup通知を設定します。
        **使い方：**
        `sk!uponoff on @up通知`
        up通知というロールにメンションするようになります。
        ロールは省略可能です。"""),
    "frrtraiseonoff": cleandoc("""FreeRTのraise通知を設定します。
        **使い方：**
        `sk!frrtraiseonoff on @fr-raise通知`
        fr-raise通知というロールにメンションするようになります。
        ロールは省略可能です。"""),
    "raiseonoff": cleandoc("""RTのraise通知を設定します。
        **使い方：**
        `sk!raiseonoff on @raise通知`
        raise通知というロールにメンションするようになります。
        ロールは省略可能です。"""),
    "freethread": cleandoc("""フリースレッド機能
        ※コマンドではありません。
        チャンネルのトピックに`sk>freethread`を入れると、
        そのチャンネルで何かを話したときに自動的にスレッドが開くようになります。"""),
    "globalchat": "グローバルチャット機能です。",
    "globalchat create": cleandoc("""グローバルチャットに参加します。
        **使い方：**
        `sk!globalchat create my_chat`
        `my_chat`という名前のグローバルチャットに接続します。
        存在しない場合は自動で作成します。
        グローバルチャット名を省略すると`main`に接続されます。"""),
    "globalchat remove": cleandoc("""グローバルチャットから切断します。
        **使い方：**
        `sk!globalchat remove`"""),
    "kaso_notice": cleandoc("""過疎通知機能です。
        **使い方：**
        `sk!kaso_notice 360`
        数字の単位は`分`です。
        この場合、360分(6時間)何もメッセージが送信されないと通知します。"""),
    "serverads": "サーバー掲示板機能です。",
    "serverads register": cleandoc("""サーバーをサーバー掲示板に登録します。
        コマンド実行後質問に答えていくだけで簡単に登録できます。"""),
    "push": cleandoc("""サーバー掲示板での表示順位を上げます。
        **使い方：**
        `sk!push`
        **注意**
        表示順位は2時間に1回しか上げることができません。"""),
    "role_linker": cleandoc("""ロールリンカー機能です。
        詳しくはこちら(リンク準備中)をご覧ください。"""),
    "role_linker set": cleandoc("""ロールリンカーを設定します。
        **使い方：**
        `sk!role_linker set [グループ名] [モード] [ロール]`
        `sk!role_linker set test sync @test1 @test2`
        test1とtest2のロールを同期モードで登録します。"""),
    "role_linker delete": cleandoc("""ロールリンカーを削除します。
        **使い方：**
        `sk!role_linker delete test`
        グループ名「test」のリンカーを削除します。"""),
}
