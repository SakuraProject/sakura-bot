# Sakura utils

from orjson import dumps as _dumps_default

from .bot import Bot
from .views import EmbedSelect, EmbedsView, TimeoutView, EmbedsButtonView
from .converters import TryConverter
from .webhooks import get_webhook

__all__ = (
    "Bot", "TryConverter",
    "EmbedSelect", "EmbedsView",
    "TimeoutView", "dumps",
    "get_webhook", "EmbedsButtonView"
)


def dumps(*args, **kwargs) -> str:
    "jsonをdumpsしてdecodeします。通常はこれを使ってください。"
    return _dumps_default(*args, **kwargs).decode()

