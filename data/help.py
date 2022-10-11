# Sakura bot - help data

from inspect import cleandoc


HELP = {
    "help": "このコマンドです。コマンドの使い方を確認することができます。",
    "playlist": "プレイリストの音楽を再生します。\n"
                "このコマンドを使用する際は先にボイスチャンネルに接続してください。",
    "captcha web": cleandoc("""Web認証用のパネルを送信します。
        **使いかた：**
        sk!captcha web ロール"""),
    "captcha password": cleandoc("""パスワード認証用のパネルを送信します。
        **使いかた：**
        sk!captcha password @認証済み 開けゴマ
        「開けゴマ」のパスワードを送信すると`@認証済み`ロールが付与されるようになります。"""),
    "gban": cleandoc("""グローバルBAN機能です。
        SakuraBotのデータベースに登録された人をそのサーバーに入ってきた時にBANすることができます。
        BAN権限がユーザーとBotにあることが条件です。""")
}
