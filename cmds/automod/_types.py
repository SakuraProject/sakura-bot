# Sakura Auto Moderation Types

from typing import TypeAlias, TypedDict, Literal

class _Setting(TypedDict, total=False):
    adminrole: list[str]
    muterole: int
    antiraid: Literal["on", "off"]
    raidaction: Literal["ban", "kick", "mute", "timeout"]
    raidactiontime: int | float | None
    ngword: list[str]


Settings: TypeAlias = dict[str, _Setting]
