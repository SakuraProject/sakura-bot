# Sakura utils

from orjson import dumps as _dumps_default

from .bot import Bot
from .views import EmbedSelect, EmbedsView, MyView, EmbedsButtonView
from .converters import TryConverter
from .webhooks import get_webhook
from ._types import GuildContext

__all__ = (
    "Bot", "TryConverter", "EmbedSelect", "EmbedsView",
    "MyView", "dumps", "get_webhook", "EmbedsButtonView",
    "GuildContext",
)


def dumps(*args, **kwargs) -> str:
    "jsonをdumpsしてdecodeします。通常はこれを使ってください。"
    return _dumps_default(*args, **kwargs).decode()
