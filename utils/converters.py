# sakura bot - Converters

from typing import TYPE_CHECKING

from discord.ext import commands


if TYPE_CHECKING:
    from typing import Annotated as TryConverter
else:
    class TryConverter:
        """An Original Converter that tries to convert some times.

        Examples
            TryConverter[discord.Guild, discord.TextChannel]
            this converter tries to convert to 2 types.
        """

        def __init__(self, converters: tuple[type[commands.Converter]]):
            self.converters = converters

        async def convert(self, ctx: commands.Context, argument: str):
            if not self.converters:
                raise ValueError("Converters not found.")
            for con in self.converters:
                try:
                    return await con.convert(ctx, argument)
                except Exception:
                    try:
                        return await con().convert(ctx, argument)
                    except Exception:
                        pass
            raise commands.BadArgument("can't be converted.")

        def __call__(self) -> None:
            pass

        def __repr__(self) -> None:
            return f'<class TryConverter([{", ".join(repr(c) for c in self.converters)}])>'

        def __class_getitem__(cls, params):
            if not isinstance(params, tuple):
                params = (params,)
            new_params = list(params)

            for param in params:
                p = commands.converter.CONVERTER_MAPPING.get(param, param)
                if isinstance(p, commands.Converter):
                    new_params.append(p)
                else:
                    if not isinstance(p, commands.Greedy | commands.Range):
                        raise TypeError(f"parameter {p!r} isn't a converter.")
                    else:
                        new_params.append(p)

            return cls(tuple(new_params))
