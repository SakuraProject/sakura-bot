# Sakura utils

from orjson import dumps as _dumps_default

from .bot import *
from .views import *
from .converters import *

__all__ = (
    "Bot", "TryConverter",
    "EmbedSelect", "EmbedsView",
    "TimeoutView", "dumps"
)

def dumps(*args, **kwargs) -> str:
    "jsonをdumpsしてdecodeします。通常はこれを使ってください。"
    return _dumps_default(*args, **kwargs).decode()

