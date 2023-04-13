from __future__ import annotations
from typing import Union, Optional, Sequence, Any, TYPE_CHECKING
import asyncio

import websockets
from orjson import loads
from websockets.exceptions import ConnectionClosed

import discord
from discord.ext import commands

from utils import Bot, dumps
from data.help import HELP

if TYPE_CHECKING:
    from discord.types.message import Message as MessageType


class WSContext(commands.Context):

    bot: Bot

    async def reply(
        self, content: Optional[str] = None, **kwargs: Any
    ) -> discord.Message:
        return await self.send(content, **kwargs)

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[discord.Embed] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        file: Optional[discord.File] = None,
        files: Optional[Sequence[discord.File]] = None,
        stickers: Optional[Sequence[Union[discord.GuildSticker, discord.StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        reference: Optional[Union[
            discord.Message, discord.MessageReference,
            discord.PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        view: Optional[discord.ui.View] = None,
        suppress_embeds: bool = False,
        ephemeral: bool = False,
    ) -> discord.Message:
        sc: str = ""
        if content is not None:
            sc = content
        if embed is not None:
            if isinstance(embed.description, str):
                sc = sc + embed.description
            if embed.fields is not None:
                for fi in embed.fields:
                    sc = sc + (fi.name or "") + (fi.value or "")
        if embeds is not None:
            for e in embeds:
                if isinstance(e.description, str):
                    sc = sc + e.description
                if e.fields is not None:
                    for fi in e.fields:
                        sc = sc + (fi.name or "") + (fi.value or "")
        sen = {
            "cmd": "send", "type": "res", "args": {"content": sc, "id": self.author.id}
        }
        return await self.bot.cogs["Websocket"].sock.send(dumps(sen))


class Websocket(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.res = {}

    async def cog_load(self):
        self.uri = "ws://sakura-bot.net:80/ws"
        self.sock = await websockets.connect(self.uri)
        self.bot.loop.create_task(self.wilp())

    async def wilp(self):
        while True:
            try:
                cmd = loads(await self.sock.recv())
                if cmd["type"] == "cmd":
                    name = cmd["cmd"]
                    res = await getattr(self, name)(cmd["args"])
                    cmd["args"] = res
                    cmd["type"] = "res"
                    recv = dumps(cmd)
                    await self.sock.send(recv)
                elif cmd["type"] == "res":
                    if not cmd["cmd"] in self.res:
                        self.res[cmd["cmd"]] = dict()
                    self.res[cmd["cmd"]][cmd["args"]["id"]] = cmd["args"]
            except ConnectionClosed:
                self.sock = await websockets.connect(self.uri)

    @commands.group()
    @commands.is_owner()
    async def backend(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @backend.command()
    async def run(self, ctx: commands.Context, *, code):
        self.res.setdefault("jsk", dict())
        self.res["jsk"][str(ctx.author.id)] = None
        req = {
            "cmd": "jsk", "type": "cmd", "args": {"id": str(ctx.author.id), "code": code}
        }
        await self.sock.send(dumps(req))
        await asyncio.sleep(1)
        while self.res["jsk"][str(ctx.author.id)] is None:
            await asyncio.sleep(1)
        await ctx.send(self.res["jsk"][str(ctx.author.id)]["res"])

    def shareguilds(self, args: dict):
        share = getattr(self.bot.get_user(int(args["id"])), "mutual_guilds", [])
        res = list()
        for g in share:
            guild = self.guild({"id": g.id})
            res.append(guild)
        return {"id": args["id"], "guilds": res}

    def guild(self, args: dict):
        g = self.bot.get_guild(args["id"])
        if not g:
            raise ValueError("Unknown Guild Id.")
        return {
            "id": str(g.id), "name": g.name, "member_count": g.member_count,
            "icon": {"url": getattr(g.icon, "url", None)},
            "text_channels": [self.channel({"id": ch.id}) for ch in g.text_channels]
        }

    def channel(self, args: dict):
        c = self.bot.get_channel(args["id"])
        if not c:
            raise ValueError("Unknown Channel Id.")
        return {"id": str(c.id), "name": getattr(c, "name", "")}

    async def invoke(self, args: dict[str, Any]):
        user = self.bot.get_user(int(args["id"]))
        if not user:
            raise ValueError("Unknown User Id.")
        payload: MessageType = {
            "id": 0, "content": args["content"], "tts": False,
            "mention_everyone": False, "attachments": [], "embeds": [],
            "author": {
                "bot": user.bot, "id": user.id, "system": user.system,
                "username": user.name, "discriminator": user.discriminator,
                "avatar": user.display_avatar.url
            },
            "edited_timestamp": None, "type": 0, "pinned": False,
            "mentions": [], "mention_roles": [], "channel_id": int(args["ch"]),
            "timestamp": ""
        }
        channel = self.bot.get_channel(int(args["ch"]))
        if not channel or not isinstance(channel, discord.abc.Messageable):
            raise ValueError("Unknown Channel Id.")
        message = discord.Message(
            data=payload, state=self.bot._get_state(), channel=channel
        )
        if channel.guild is not None:
            message.author = channel.guild.get_member(user.id)  # type: ignore
        else:
            message.author = user
        ctx = await self.bot.get_context(message, cls=WSContext)
        await self.bot.invoke(ctx)
        return args

    def help_catlist(self, args: dict) -> dict:
        "カテゴリのリストを'res'に入れて返す。"
        args["res"] = [
            {"rname": name, "name": name}
            for name in self.bot.cogs["Help"].get_categories()
        ]
        return args

    async def help_cmdlist(self, args: dict) -> dict:
        "コマンドのリストを'res'に入れて返す。"
        cmds = list()
        l = args["l"]
        for c in [m for m in self.bot.cogs.values(
        ) if m.__module__.startswith("cogs." + args["id"])]:
            if not isinstance(c, commands.Cog):
                continue
            for cm in c.get_commands():
                cmds.append(self.command({"id": cm.name}))
        args["res"] = cmds
        return args

    def command(self, args: dict) -> dict:
        "コマンドの情報を'res'に入れて返す。argsの'id'にはコマンド名を入れること。"
        cm = self.bot.get_command(args["id"])
        if not cm:
            return args
        dc = {
            "name": args["id"], "doc": HELP.get(cm.name, ""), "type": type(cm).__name__,
            "clean_params": [self.convert_param(p) for p in cm.clean_params.values()],
        }
        if isinstance(cm, commands.Group | commands.HybridGroup):
            dc["commands"] = [
                self.command({"id": f"{cm.name} {c.name}"}) for c in cm.commands
            ]
        args["res"] = dc
        return args

    def convert_param(self, p: commands.Parameter):
        return {"name": p.name, "required": p.required}

    def commands(self, args):
        ccl = list()
        for c in self.bot.commands:
            if isinstance(c, commands.Group | commands.HybridGroup):
                comds = c.commands
                for cm in comds:
                    if isinstance(cm, commands.Group | commands.HybridGroup):
                        comds1 = list(cm.commands)
                        for ccm in comds1:
                            ccl.append(self.command(
                                {"id": c.name + " " + cm.name + " " + ccm.name}
                            ))
                    else:
                        ccl.append(self.command({"id": c.name + " " + cm.name}))
            else:
                ccl.append(self.command({"id": c.name}))
        args["commands"] = ccl
        return args


def setup(bot: Bot):
    return bot.add_cog(Websocket(bot))
