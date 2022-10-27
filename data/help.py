# Sakura bot - help data

from inspect import cleandoc


HELP = {
    "help": "このコマンドです。コマンドの使い方を確認することができます。",
    "about": "Botの情報を見ることができます。",
    "ping": cleandoc("""pingを調べることができます。
        botの速さを調べられます。単位はms(ミリ秒)です。
        1000msを超えるようなことがあればサポートサーバーにて報告してください。"""),
    "captcha": cleandoc("""認証機能です。
        サーバーを荒らしから守るために使用できます。"""),
    "captcha web": cleandoc("""Web認証用のパネルを送信します。
        **使いかた：**
        sk!captcha web @認証済み
        実行すると、webサイトへのボタンを含むメッセージが送信されます。"""),
    "captcha password": cleandoc("""パスワード認証用のパネルを送信します。
        **使いかた：**
        sk!captcha password @認証済み 開けゴマ
        「開けゴマ」のパスワードを送信すると`@認証済み`ロールが付与されるようになります。"""),
    "gban": cleandoc("""グローバルBAN機能です。
        SakuraBotのデータベースに登録された人をそのサーバーに入ってきた時にBANすることができます。
        BAN権限がユーザーとBotにあることが条件です。"""),
}
