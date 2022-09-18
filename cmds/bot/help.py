import importlib
import os

import discord
from discord.ext import commands

from utils import Bot


class Help(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot, self.before = bot, ""
        self.helps = {}

    @commands.command(
        aliases=["ヘルプ"]
    )
    async def help(self, ctx: commands.Context, cmd=None, subcmd=None):
        """
        NLang ja ヘルプを表示します
        あなたが今実行しているコマンドです。ヘルプを表示します
        **使いかた：**
        EVAL self.bot.command_prefix+'help'
        EVAL self.bot.command_prefix+'help コマンド名'
        ELang ja
        NLang default SHow Help
        Is the command you are running now
        **How to use：**
        EVAL self.bot.command_prefix+'help'
        EVAL self.bot.command_prefix+'help command name'
        ELang default
        """
        embed = await self.create_help(cmd, subcmd)
        view = discord.ui.View()
        view.add_item(CatList(self))
        await ctx.send(embed=embed, view=view)

    async def create_help(self, cmd=None, subcmd=None) -> discord.Embed:
        l = "ja"
        sed = "これはBotのヘルプです。下の選択メニューからカテゴリを選ぶことによりコマンドを選択できます。これを見てもよくわからない方はサポートサーバーまでお問い合わせください"
        prefix = self.bot.command_prefix if isinstance(self.bot.command_prefix, str) else "/"
        if cmd is not None:
            if subcmd is None:
                comd = self.bot.get_command(cmd)
                assert comd
                if isinstance(comd, commands.Group | commands.HybridGroup):
                    comds = list(comd.commands)
                    sed = ""
                    for gcm in comds:
                        if gcm.callback.__doc__ is not None:
                            doc = await self.parsedoc(gcm.callback.__doc__)
                            try:
                                sed = sed + prefix + comd.name + \
                                    " " + gcm.name + " : " + \
                                    doc["sd"][l] + "\n"
                            except KeyError:
                                sed = sed + prefix + comd.name + \
                                    " " + gcm.name + " : " + \
                                    doc["sd"]["default"] + "\n"
                        else:
                            sed = sed + prefix + comd.name + " " + gcm.name + " : \n"
                elif isinstance(comd, commands.Command | commands.HybridCommand):
                    if comd.callback.__doc__ is not None:
                        doc = await self.parsedoc(comd.callback.__doc__)
                        try:
                            sed = doc["desc"][l]
                        except KeyError:
                            sed = doc["desc"]["default"]
                    else:
                        sed = "このコマンドの詳細はサポートサーバーでお問い合わせください"
            else:
                comd = self.bot.get_command(cmd + " " + subcmd)
                assert comd
                if type(comd).__name__ == "Command" or type(comd).__name__ == "HybridCommand":
                    if comd.callback.__doc__ is not None:
                        doc = await self.parsedoc(comd.callback.__doc__)
                        try:
                            sed = doc["desc"][l]
                        except KeyError:
                            sed = doc["desc"]["default"]
                    else:
                        sed = "このコマンドの詳細はサポートサーバーでお問い合わせください"
        return discord.Embed(color=self.bot.Color, description=sed)

    async def parsedoc(self, doc):
        spl = doc.splitlines()
        lang = dict()
        res = dict()
        sdesc = dict()
        dol = False
        dln = ""
        for cmds in spl:
            cmds = cmds.replace("    ", "")
            cmd = cmds.split(" ")
            if cmd[0] == "NLang":
                dol = True
                dln = cmd[1]
                sdesc[dln] = cmds.replace("NLang " + dln + " ", "")
                lang[dln] = ""
                continue
            if cmd[0] == "ELang":
                dol = False
                dln = ""
                continue
            if dol:
                if cmd[0] == "EVAL":
                    lang[dln] = lang[dln] + \
                        eval(cmds.replace("EVAL ", "")) + "\n"
                else:
                    lang[dln] = lang[dln] + cmds + "\n"
        res["sd"] = sdesc
        res["desc"] = lang
        return res


class CatList(discord.ui.Select):
    def __init__(self, cog):
        l = "ja"
        self.cog = cog
        options = []
        for name in os.listdir("cmds"):
            if not name.startswith((".", "_")):
                try:
                    name = importlib.import_module(f"cmds.{name}").name
                    try:
                        rname = eval(name)[l]
                    except KeyError:
                        rname = eval(name)["default"]
                except AttributeError:
                    rname = name
                options.append(discord.SelectOption(
                    label=name, description='', value=rname))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        bot = self.cog.bot
        sed = ""
        cmds = list()
        l = "ja"
        view = discord.ui.View()
        for c in [m for m in bot.cogs.values() if m.__module__.startswith("cmds."+self.values[0])]:
            for cm in c.get_commands():
                if cm.callback.__doc__ != None:
                    doc = await self.cog.parsedoc(cm.callback.__doc__)
                    try:
                        sed = sed + self.cog.bot.command_prefix + \
                            cm.name + " : " + doc["sd"][l] + "\n"
                    except KeyError:
                        sed = sed + self.cog.bot.command_prefix + \
                            cm.name + " : " + doc["sd"]["default"] + "\n"
                else:
                    sed = sed + self.cog.bot.command_prefix + cm.name + " : \n"
                cmds.append(cm)
        ebd = discord.Embed(color=self.cog.bot.Color, description=sed)
        view.add_item(self)
        view.add_item(CmdList(cmds, self.cog))
        await interaction.response.edit_message(embeds=[ebd], view=view)


class CmdList(discord.ui.Select):
    def __init__(self, cmds, cog):
        self.cog = cog
        options = []
        self.cmds = cmds
        for cm in cmds:
            if cm.parent == None:
                options.append(discord.SelectOption(
                    label=self.cog.bot.command_prefix + cm.name, description='', value=cm.name))
            else:
                options.append(discord.SelectOption(label=self.cog.bot.command_prefix + cm.parent.qualified_name +
                               " " + cm.name, description='', value=cm.parent.qualified_name + " " + cm.name))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        bot = self.cog.bot
        val = self.values[0]
        cmd = bot.get_command(val)
        if type(cmd).__name__ == "Command" or type(cmd).__name__ == "HybridCommand":
            if cmd.parent != None:
                spl = val.split(" ")
                hl = await self.cog.hpl(spl[0], spl[1])
            else:
                hl = await self.cog.hpl(val)
            ebd = hl["ebd"]
            await interaction.response.edit_message(embeds=[ebd])
        else:
            hl = await self.cog.hpl(val)
            ebd = hl["ebd"]
            view = discord.ui.View()
            view.add_item(CatList(self.cog))
            view.add_item(CmdList(list(cmd.commands), self.cog))
            await interaction.response.edit_message(embeds=[ebd], view=view)


async def setup(bot: Bot):
    await bot.add_cog(Help(bot))
