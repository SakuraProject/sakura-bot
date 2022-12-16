# Sakura Bot Utils - Alternative Private Functions

from typing import TypeVar, Any

cogT = TypeVar("cogT", bound=Any)
class automod:
    @staticmethod
    def raidcheck(cog: cogT, member) -> tuple[cogT, bool]:
        "メンバーがレイドかどうかチェックします。"
        return cog, False
