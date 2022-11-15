from typing import Union, Optional, Sequence, Any

import asyncio

import websockets
from orjson import loads
from websockets.exceptions import ConnectionClosed

import discord
from discord.ext import commands

from utils import Bot, dumps
from data.help import HELP


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
        sen: dict[str, str | dict] = {"cmd": "send", "type": "res"}
        args = {"content": sc, "id": self.author.id}
        sen["args"] = args
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
    async def run(self, ctx, *, code):
        self.res.setdefault("jsk", dict())
        self.res["jsk"][str(ctx.author.id)] = None
        req = dict()
        req["cmd"] = "jsk"
        req["type"] = "cmd"
        arg = dict()
        arg["id"] = str(ctx.author.id)
        arg["code"] = code
        req["args"] = arg
        await self.sock.send(dumps(req))
        await asyncio.sleep(1)
        while self.res["jsk"][str(ctx.author.id)] is None:
            await asyncio.sleep(1)
        await ctx.send(self.res["jsk"][str(ctx.author.id)]["res"])

    async def shareguilds(self, args: dict):
        share = getattr(self.bot.get_user(int(args["id"])), "mutual_guilds", [])
        res = list()
        for g in share:
            guild = await self.guild({"id": g.id})
            res.append(guild)
        recv = dict()
        recv["id"] = args["id"]
        recv["guilds"] = res
        return recv

    async def guild(self, args: dict):
        g = self.bot.get_guild(args["id"])
        if not g:
            raise ValueError("Unknown Guild Id.")
        guild = {}
        guild["id"] = str(g.id)
        guild["name"] = g.name
        guild["member_count"] = g.member_count
        guild["icon"] = dict()
        if g.icon is not None:
            guild["icon"]["url"] = g.icon.url
        else:
            guild["icon"]["url"] = None
        guild["text_channels"] = [(await self.channel({"id": ch.id})) for ch in g.text_channels]
        return guild

    async def channel(self, args: dict):
        g = self.bot.get_channel(args["id"])
        if not g:
            raise ValueError("Unknown Channel Id.")
        ch = dict()
        ch["id"] = str(g.id)
        ch["name"] = getattr(g, "name", "")
        return ch

    async def invoke(self, args: dict[str, Any]):
        payload: dict[str, Any] = {
            "id": 0, "content": args["content"], "tts": False,
            "mention_everyone": False, "attachments": [], "embeds": [],
        }
        user = self.bot.get_user(int(args["id"]))
        if not user:
            raise ValueError("Unknown User Id.")
        aut = {"bot": user.bot, "id": user.id, "system": user.system}
        payload["author"] = aut
        payload["edited_timestamp"] = None
        payload["type"] = 0
        payload["pinned"] = False
        payload["mentions"] = []
        payload["mention_roles"] = []
        message = discord.Message(data=payload, state=self.bot._get_state(
        ), channel=self.bot.get_channel(int(args["ch"])))
        g = self.bot.get_channel(int(args["ch"])).guild
        if g is not None:
            message.author = g.get_member(int(args["id"]))
        else:
            message.author = user
        ctx = await self.bot.get_context(message, cls=WSContext)
        await self.bot.invoke(ctx)
        return args

    async def help_catlist(self, args: dict) -> dict:
        "カテゴリのリストを'res'に入れて返す。"
        options = [
            {"rname": name, "name": name}
            for name in self.bot.cogs["Help"].get_categories()
        ]
        args["res"] = options
        return args

    async def help_cmdlist(self, args: dict) -> dict:
        "コマンドのリストを'res'に入れて返す。"
        cmds = list()
        l = args["l"]
        for c in [m for m in self.bot.cogs.values(
        ) if m.__module__.startswith("cogs." + args["id"])]:
            for cm in c.get_commands():
                cmds.append(await self.command({"id": cm.name}))
        args["res"] = cmds
        return args

    async def command(self, args: dict) -> dict:
        "コマンドの情報を'res'に入れて返す。argsの'id'にはコマンド名を入れること。"
        cm = self.bot.get_command(args["id"])
        if not cm:
            return args
        dc = dict()
        if isinstance(cm, commands.Group | commands.HybridGroup):
            comds = list(cm.commands)
            cl = list()
            for c in comds:
                cl.append(await self.command({"id": cm.name + " " + c.name}))
            dc["commands"] = cl
        dc["name"] = args["id"]
        clp = [(await self.convert_param(p))
               for p in cm.clean_params.values()]
        dc["clean_params"] = clp
        dc["doc"] = HELP.get(cm.name, "")
        dc["type"] = type(cm).__name__
        args["res"] = dc
        return args

    async def convert_param(self, p: commands.Parameter):
        return {"name": p.name, "required": p.required}

    async def commands(self, args):
        ccl = list()
        for c in self.bot.commands:
            if isinstance(c, commands.Group | commands.HybridGroup):
                comds = c.commands
                for cm in comds:
                    if isinstance(cm, commands.Group | commands.HybridGroup):
                        comds1 = list(cm.commands)
                        for ccm in comds1:
                            ccl.append(await self.command(
                                {"id": c.name + " " + cm.name + " " + ccm.name}
                            ))
                    else:
                        ccl.append(await self.command({"id": c.name + " " + cm.name}))
            else:
                ccl.append(await self.command({"id": c.name}))
        args["commands"] = ccl
        return args


def setup(bot: Bot):
    return bot.add_cog(Websocket(bot))
