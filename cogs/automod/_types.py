# Sakura Auto Moderation Types

from typing import TypeAlias, TypedDict, Literal

Actions: TypeAlias = Literal["ban", "kick", "mute", "timeout", "none"]


class Setting(TypedDict, total=True):
    "セッティング情報。"
    adminrole: list[str]  # 管理者ロール
    modrole: list[str]  # モデレーターロール
    muterole: int  # ミュートされた人用ロール

    antiraid: Literal["on", "off"]  # レイド対策ONOFF
    raidaction: Actions  # レイドが起こった時のアクション
    raidactiontime: int | float  # レイドアクションの時間
    raidcount: int  # レイド判定用のカウント

    ignore_channel: list[int]  # 例外チャンネル一覧
    ignore_role: list[int]  # 例外ロール一覧

    ngword: list[str]  # NGワード一覧

    duplct: int  # ストライクポイント付与のためのspam回数
    action: dict[str, Actions | str]  # ストライクポイントによるアクション

    tokens: Literal["on", "off"]  # トークン保護のオンオフ


class MutedUser(TypedDict, total=False):
    "ミュート・BANされたユーザーのデータ。"
    type: Literal["ban", "mute"]
    time: int
