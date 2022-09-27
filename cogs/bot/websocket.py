import discord
from discord.ext import commands
import asyncio
import websockets
from ujson import loads, dumps
from websockets.exceptions import ConnectionClosed
from discord.ext.commands import Context
from typing import Union, Optional, Sequence, Any
from discord.sticker import GuildSticker, StickerItem
from discord.mentions import AllowedMentions
from discord.message import MessageReference, PartialMessage
from discord.ui import View
from discord import Embed, File, Message
import os


class WSContext(Context):

    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        await self.send(content, **kwargs)

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[Embed] = None,
        embeds: Optional[Sequence[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message,
                                  MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        view: Optional[View] = None,
        suppress_embeds: bool = False,
        ephemeral: bool = False,
    ) -> Message:
        sc = ""
        if content is not None:
            sc = content
        if embed is not None:
            if isinstance(embed.description, str):
                sc = sc + embed.description
            if embed.fields is not None:
                for fi in embed.fields:
                    sc = sc + fi.name + fi.value
        if embeds is not None:
            for e in embeds:
                if isinstance(e.description, str):
                    sc = sc + embed.description
                if e.fields is not None:
                    for fi in e.fields:
                        sc = sc + fi.name + fi.value
        sen = dict()
        sen["cmd"] = "send"
        args = dict()
        args["content"] = sc
        args["id"] = str(self.author.id)
        sen["args"] = args
        sen["type"] = "res"
        await self.bot.cogs["websocket"].sock.send(dumps(sen))


class websocket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.res = dict()

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
    async def backend(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @backend.command()
    @commands.is_owner()
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

    async def shareguilds(self, args):
        share = [g for g in self.bot.guilds if g.get_member(
            int(args["id"])) is not None]
        res = list()
        for g in share:
            guild = await self.guild({"id": g.id})
            res.append(guild)
        recv = dict()
        recv["id"] = args["id"]
        recv["guilds"] = res
        return recv

    async def guild(self, args):
        g = self.bot.get_guild(args["id"])
        guild = dict()
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

    async def channel(self, args):
        g = self.bot.get_channel(args["id"])
        ch = dict()
        ch["id"] = str(g.id)
        ch["name"] = g.name
        return ch

    async def invoke(self, args):
        payload = dict()
        payload["id"] = 0
        user = self.bot.get_user(int(args["id"]))
        aut = dict()
        aut["bot"] = user.bot
        aut["id"] = user.id
        aut["system"] = user.system
        payload["author"] = aut
        payload["content"] = args["content"]
        payload["tts"] = False
        payload["mention_everyone"] = False
        payload["attachments"] = []
        payload["embeds"] = []
        payload["edited_timestamp"] = None
        payload["type"] = 0
        payload["pinned"] = False
        payload["mentions"] = []
        payload["mention_roles"] = []
        message = discord.message.Message(data=payload, state=self.bot._get_state(
        ), channel=self.bot.get_channel(int(args["ch"])))
        g = self.bot.get_channel(int(args["ch"])).guild
        if g is not None:
            message.author = g.get_member(int(args["id"]))
        else:
            message.author = user
        ctx = await self.bot.get_context(message, cls=WSContext)
        await self.bot.invoke(ctx)
        return args

    async def help_catlist(self, args):
        options = []
        for name in os.listdir("cogs"):
            if not name.startswith((".", "_")):
                try:
                    exec("from cogs." + name + " import name as " + name)
                    try:
                        rname = eval(name)[args["l"]]
                    except KeyError:
                        rname = eval(name)["default"]
                except ImportError:
                    rname = name
                data = dict()
                data["rname"] = rname
                data["name"] = name
                options.append(data)
        args["res"] = options
        return args

    async def help_cmdlist(self, args):
        bot = self.bot
        cmds = list()
        l = args["l"]
        for c in [m for m in bot.cogs.values() if m.__module__.startswith("cogs."+args["id"])]:
            for cm in c.get_commands():
                cmds.append(await self.command({"id": cm.name}))
        args["res"] = cmds
        return args

    async def command(self, args):
        cm = self.bot.get_command(args["id"])
        dc = dict()
        if type(cm).__name__ == "Group" or type(cm).__name__ == "HybridGroup":
            comds = list(cm.commands)
            cl = list()
            for c in comds:
                cl.append(await self.command({"id": cm.name + " " + c.name}))
            dc["commands"] = cl
        dc["name"] = args["id"]
        clp = list()
        for ckey in cm.clean_params.keys():
            clp.append(await self.convert_param(cm.clean_params[ckey]))
        dc["clean_params"] = clp
        if cm.callback.__doc__ is not None:
            dc["doc"] = await self.bot.cogs["help"].parsedoc(cm.callback.__doc__)
        dc["type"] = type(cm).__name__
        args["res"] = dc
        return args

    async def convert_param(self, p):
        res = dict()
        res["name"] = p.name
        res["required"] = p.required
        return res

    async def commands(self, args):
        ccl = list()
        for c in self.bot.commands:
            if type(c).__name__ == "Group" or type(c).__name__ == "HybridGroup":
                comds = list(c.commands)
                for cm in comds:
                    if type(cm).__name__ == "Group" or type(cm).__name__ == "HybridGroup":
                        comds1 = list(cm.commands)
                        for ccm in comds1:
                            ccl.append(await self.command({"id": c.name + " " + cm.name + " " + ccm.name}))
                    else:
                        ccl.append(await self.command({"id": c.name + " " + cm.name}))
            else:
                ccl.append(await self.command({"id": c.name}))
        args["commands"] = ccl
        return args


def setup(bot):
    return bot.add_cog(websocket(bot))
