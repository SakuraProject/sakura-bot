"""New Automod
新AutoModシステム。
"""

from typing import Literal

from discord.ext import commands, tasks
import discord
from pytimeparse.timeparse import timeparse
from datetime import timedelta
from ujson import loads, dumps
import time
import re

from core import Bot

from .types import Setting


def arrayinarray(list1, list2) -> bool:
    "list1の項目がlist2の中に一つでも含まれているかをチェックします。"
    return any(item in list2 for item in list1)

class AutoMod(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings: dict[str, Setting] = dict()
        self.punishments = dict()
        self.muteds = dict()
        self.m = dict()
        self.time_ = dict()
        self.sendtime = dict()
        self.sendcont = dict()
        self.sendmsgs = dict()
        self.sendcount = dict()
        self.untask.start()

    async def cog_load(self):
        ctsql = """CREATE TABLE if not exists AutoMod (
            GuildId BIGINT NOT NULL,
            Setting JSON NOT NULL,
            Strike JSON NOT NULL,
            Muted JSON NOT NULL
        ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"""

        async def sqling(cursor):
            await cursor.execute(ctsql)
            await cursor.execute("SELECT * FROM AutoMod")
            return await cursor.fetchall()

        res = await self.bot.execute_sql(sqling)

        for row in res:
            self.settings[str(row[0])] = loads(row[1])
            self.punishments[str(row[0])] = loads(row[2])
            self.muteds[str(row[0])] = loads(row[3])

    @commands.group()
    async def automod(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        await ctx.send("使い方が違います。")

    async def check_permissions(
        self, type_: Literal["admin", "manage-guild"], ctx: commands.Context
    ) -> None:
        "ctx.authorが特定のtypeの権限を持っているか確認します。持っていなければエラーを送出します。"
        if type_ == "admin" and not (
            ctx.author.guild_permissions.administrator
            or arrayinarray(
                [r.id for r in ctx.author.roles],
                self.settings[str(ctx.guild.id)]['adminrole']
            )
        ):
            return self.raise_missing_parms(ctx, ["administrator"])
        if type == "manage-guild" and not (
            ctx.author.guild_permissions.manage_guild
            or arrayinarray(
                [r.id for r in ctx.author.roles],
                self.settings[str(ctx.guild.id)]['adminrole']
            ) or arrayinarray(
                [r.id for r in ctx.author.roles],
                self.settings[str(ctx.guild.id)]['modrole']
            )
        ):
            return self.raise_missing_parms(ctx, ["manage_guild"])

    @tasks.loop(seconds=10)
    async def untask(self):
        # Unban / unmute用のループ。
        now = int(time.time())
        for gid in self.muteds:
            g = self.bot.get_guild(int(gid))
            for uid in self.muteds[gid].keys():
                if int(self.muteds[gid][uid]["time"]) < now:
                    try:
                        if self.muteds[gid][uid]["type"] == "ban":
                            member = await self.bot.fetch_user(int(uid))
                            await g.unban(member)
                        elif self.muteds[gid][uid]["type"] == "mute":
                            member = g.get_member(int(uid))
                            await member.remove_roles(g.get_role(self.settings[str(gid)]["muterole"]))
                    except:
                        pass

    @commands.command()
    async def muterolesetup(self, ctx, role: discord.Role = None):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = {"adminrole": []}
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = []

        await self.check_permissions("admin", ctx)

        if role is None:
            role = await ctx.guild.create_role(name="sakura Muted", color=self.bot.Color)
        for tc in ctx.guild.text_channels:
            overwrite = tc.overwrites_for(role)
            overwrite.update(**{"send_messages": False, "add_reactions": False,
                             "create_public_threads": False, "send_messages_in_threads": False})
            overwrites = tc.overwrites
            overwrites[role] = overwrite
            await tc.edit(overwrites=overwrites)
        for tc in ctx.guild.voice_channels:
            overwrite = tc.overwrites_for(role)
            overwrite.update(
                **{"send_messages": False, "add_reactions": False, "connect": False, "speak": False})
            overwrites = tc.overwrites
            overwrites[role] = overwrite
            await tc.edit(overwrites=overwrites)
        self.settings[str(ctx.guild.id)]["muterole"] = role.id
        await self.save(ctx.guild.id)
        await ctx.send("Ok")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        try:
            role = channel.guild.get_role(
                int(self.settings[str(channel.guild.id)]["muterole"]))
            overwrite = channel.overwrites_for(role)
            overwrite.update(**{"send_messages": False, "add_reactions": False, "create_public_threads": False,
                             "send_messages_in_threads": False, "connect": False, "speak": False})
            overwrites = channel.overwrites
            overwrites[role] = overwrite
            await channel.edit(overwrites=overwrites)
        except discord.Forbidden:
            pass

    def raidcheck(self, member):
        if not str(member.guild.id) in self.m:
            self.m[str(member.guild.id)] = list()
        if not str(member.guild.id) in self.time_:
            self.time_[str(member.guild.id)] = time.time()
        self.m[str(member.guild.id)].append(member)
        if time.time() - self.time_[str(member.guild.id)] >= 15.0:
            self.time_[str(member.guild.id)] = time.time()
            if time.time() - self.time_[str(member.guild.id)] >= 60.0:
                self.m[str(member.guild.id)] = list()
        elif len(self.m[str(member.guild.id)]) >= int(self.settings[str(member.guild.id)]['raidcount']) and time.time() - self.time_[str(member.guild.id)] <= 15.0:
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.settings.setdefault(str(member.guild.id), dict())
        self.settings[str(member.guild.id)].setdefault('antiraid', 'off')
        if self.settings[str(member.guild.id)]['antiraid'] == 'on':
            if self.raidcheck(member):
                if self.settings[str(member.guild.id)]['raidaction'] == 'ban':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.ban(reason="sakura anti raid")
                if self.settings[str(member.guild.id)]['raidaction'] == 'kick':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.kick(reason="sakura anti raid")
                if self.settings[str(member.guild.id)]['raidaction'] == 'mute':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.add_roles(int(member.guild.get_role(self.settings[str(member.guild.id)]["muterole"])), reason="sakura anti raid")
                        if not str(member.guild.id) in self.muteds:
                            self.muteds[str(member.guild.id)] = dict()
                        if self.settings[str(member.guild.id)]['raidactiontime'] != None:
                            self.muteds[str(member.guild.id)
                                        ][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(
                                time.time()) + int(self.settings[str(member.guild.id)]['raidactiontime'])
                            self.muteds[str(member.guild.id)][str(
                                memb.id)]["type"] = "mute"
                    await self.save(member.guild.id)
                if self.settings[str(member.guild.id)]['raidaction'] == 'timeout':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.timeout(timedelta(seconds=int(self.settings[str(member.guild.id)]['raidactiontime'])), reason="sakura anti raid")

    @commands.group()
    async def ngword(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @ngword.command()
    async def set(self, ctx, *, word):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not "ngword" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["ngword"] = list()
        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            await ctx.send("すでに設定されています")
        else:
            self.settings[str(ctx.guild.id)]["ngword"].append(word)
            await ctx.send("設定しました")
            await self.save(ctx.guild.id)

    @ngword.command()
    async def remove(self, ctx, *, word):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not "ngword" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["ngword"] = list()
        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            self.settings[str(ctx.guild.id)]["ngword"].pop(word)
            await ctx.send("削除しました")
            await self.save(ctx.guild.id)
        else:
            await ctx.send("設定されていません")

    @commands.command()
    async def antiraid(self, ctx, joincount: int, action='kick', time=None):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if time != None:
            time = timeparse(time)
        if action == 'kick':
            self.settings[str(ctx.guild.id)].update(
                {"antiraid": "on", "raidcount": joincount, "raidaction": action})
            await ctx.send("設定をonにしました")

        if action == 'ban':
            self.settings[str(ctx.guild.id)].update(
                {"antiraid": "on", "raidcount": joincount, "raidaction": action, 'raidactiontime': time})
            await ctx.send("設定をonにしました")

        if action == 'mute':
            self.settings[str(ctx.guild.id)].update(
                {"antiraid": "on", "raidcount": joincount, "raidaction": action, 'raidactiontime': time})
            await ctx.send("設定をonにしました")
        if action == 'timeout':
            self.settings[str(ctx.guild.id)].update(
                {"antiraid": "on", "raidcount": joincount, "raidaction": action, 'raidactiontime': time})
            await ctx.send("設定をonにしました")
        if action == 'none':
            self.settings[str(ctx.guild.id)].update(
                {"antiraid": "off", "raidcount": joincount, "raidaction": action})
            await ctx.send("設定をoffにしました")
        await self.save(ctx.guild.id)

    @commands.command()
    async def ignore(self, ctx, id: int = 0):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not "ch" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["ch"] = list()
        if not "role" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["role"] = list()
        if id == 0:
            id = ctx.channel.id
        ch = ctx.guild.get_channel(id)
        role = ctx.guild.get_role(id)
        if ch != None:
            self.settings[str(ctx.guild.id)]["ch"].append(id)
            await ctx.send("設定完了しました")
            await self.save(ctx.guild.id)
        elif role != None:
            self.settings[str(ctx.guild.id)]["role"].append(id)
            await ctx.send("設定完了しました")
            await self.save(ctx.guild.id)

    def ig(self, msg) -> bool:
        if not str(msg.guild.id) in self.settings:
            self.settings[str(msg.guild.id)] = dict()
        if not "ch" in self.settings[str(msg.guild.id)]:
            self.settings[str(msg.guild.id)]["ch"] = list()
        if not "role" in self.settings[str(msg.guild.id)]:
            self.settings[str(msg.guild.id)]["role"] = list()
        if msg.channel.id in self.settings[str(msg.guild.id)]["ch"]:
            return True
        try:
            for y in msg.author.roles:
                rid = y.id
                if rid in self.settings[str(msg.guild.id)]["role"]:
                    return True
        except:
            return False
        return False

    @commands.command()
    async def antitokens(self, ctx, onoff):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if onoff == 'on':
            self.settings[str(ctx.guild.id)]['tokens'] = 'on'
            await self.save(ctx.guild.id)
            await ctx.send('antitokenモードをonにしました')
        if onoff == 'off':
            self.settings[str(ctx.guild.id)]['tokens'] = 'off'
            await self.save(ctx.guild.id)
            await ctx.send('antitokenモードをoffにしました')

    @commands.command()
    async def punishment(self, ctx, strike, modaction, sec=None):
        if sec != None:
            sec = timeparse(sec)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole'] = list()
        await self.check_permissions("manage-guild", ctx)
        stri = int(strike)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "action" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['action'] = dict()
        if modaction == 'ban' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(
                stri)] = 'ban,'+str(int(sec))
        elif modaction == 'ban':
            self.settings[str(ctx.guild.id)]['action'][str(stri)] = 'ban'
        if modaction == 'mute' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(
                stri)] = 'mute,'+str(int(sec))
        elif modaction == 'mute':
            self.settings[str(ctx.guild.id)]['action'][str(stri)] = 'mute'
        if modaction == 'kick':
            self.settings[str(ctx.guild.id)]['action'][str(stri)] = 'kick'
        if modaction == 'timeout' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(
                stri)] = 'timeout,'+str(int(sec))
        if modaction == 'none':
            self.settings[str(ctx.guild.id)]['action'][str(stri)] = 'None'
        await self.save(ctx.guild.id)
        await ctx.send(str(stri)+'に'+str(modaction)+'を設定しました')

    @commands.command()
    async def antispam(self, ctx, spamcount: int):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        self.settings[str(ctx.guild.id)]['duplct'] = spamcount
        await self.save(ctx.guild.id)
        await ctx.send(str(spamcount)+'回連投で1Strike付与します')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def pardon(self, ctx, id: int, strikes=1):
        self.punishments[str(ctx.guild.id)][str(
            id)] = self.punishments[str(ctx.guild.id)][str(id)]-strikes
        await ctx.send("pardoned "+str(strikes)+"strikes on"+str(id))
        await self.save(ctx.guild.id)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def check(self, ctx, id: int):
        await ctx.send(str(id)+"has"+str(self.punishments[str(ctx.guild.id)][str(id)])+"strikes")

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole'] = list()
        await self.check_permissions("manage-guild", ctx)
        await member.add_roles(ctx.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
        await ctx.send(f"{member.mention}をmuteしました。")

    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole'] = list()
        await self.check_permissions("manage-guild", ctx)
        await member.remove_roles(ctx.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
        await ctx.send(f"{member.mention}をunmuteしました。")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id == self.bot.user.id:
            return
        if msg.guild.get_member(msg.author.id) != None:
            msg.author = msg.guild.get_member(msg.author.id)
        try:
            if self.settings[str(msg.guild.id)]['tokens'] == 'on':
                tkreg = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'
                if re.search(tkreg, msg.content) != None:
                    userid = msg.author.id
                    guildid = msg.guild.id
                    if not str(msg.guild.id) in self.punishments:
                        self.punishments[str(msg.guild.id)] = dict()
                    if not str(userid) in self.punishments[str(msg.guild.id)]:
                        self.punishments[str(msg.guild.id)][str(userid)] = 0
                    self.punishments[str(msg.guild.id)][str(
                        userid)] = self.punishments[str(msg.guild.id)][str(userid)]+1
                    punish = self.punishments[str(msg.guild.id)][str(userid)]
                    await msg.delete()
                    await msg.channel.send("tokenの送信はこのサーバーで禁止されています")
                    userid = msg.author.id
                    try:
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban'):
                            if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban,'):
                                self.muteds[str(msg.guild.id)
                                            ][str(userid)] = dict()
                                self.muteds[str(msg.guild.id)][str(userid)]["time"] = int(time.time(
                                )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('ban,', ''))
                                self.muteds[str(msg.guild.id)][str(
                                    userid)]["type"] = "ban"
                            await msg.author.ban()
                        if self.settings[str(msg.guild.id)]['action'][str(punish)] == 'kick':
                            await msg.author.kick()
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute'):
                            if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute,'):
                                self.muteds[str(msg.guild.id)
                                            ][str(userid)] = dict()
                                self.muteds[str(msg.guild.id)][str(userid)]["time"] = int(time.time(
                                )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('mute,', ''))
                                self.muteds[str(msg.guild.id)][str(
                                    userid)]["type"] = "mute"
                            await msg.author.add_roles(msg.guild.get_role(self.settings[str(msg.guild.id)]["muterole"]))
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('timeout'):
                            await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('timeout,', ''))), reason="sakura automod")
                    except KeyError:
                        pass
                    await self.save(msg.guild.id)
        except KeyError:
            pass
        if self.ig(msg):
            return

        # デフォルトの設定
        self.sendcount.setdefault(str(msg.guild.id), dict())
        self.sendcount[str(msg.guild.id)].setdefault(str(msg.author.id), '')

        self.sendmsgs.setdefault(str(msg.guild.id), dict())
        self.sendmsgs[str(msg.guild.id)].setdefault(str(msg.author.id), list())

        self.sendtime.setdefault(str(msg.guild.id), dict())
        self.sendtime[str(msg.guild.id)].setdefault(str(msg.author.id), time.time())
        
        self.sendcont.setdefault(str(msg.guild.id), dict())
        self.sendcont[str(msg.guild.id)].setdefault(str(msg.author.id), '')

        if time.time() - self.sendtime[str(msg.guild.id)][str(msg.author.id)] <= 2.0:
            self.sendtime[str(msg.guild.id)][str(msg.author.id)] = time.time()
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)].append(msg)
            if not str(msg.guild.id) in self.settings:
                self.settings[str(msg.guild.id)] = dict()
            if not 'duplct' in self.settings[str(msg.guild.id)]:
                self.settings[str(msg.guild.id)]['duplct'] = 5
            if len(self.sendmsgs[str(msg.guild.id)][str(msg.author.id)]) >= int(self.settings[str(msg.guild.id)]['duplct']):
                userid = msg.author.id
                if not str(msg.guild.id) in self.punishments:
                    self.punishments[str(msg.guild.id)] = dict()
                if not str(userid) in self.punishments[str(msg.guild.id)]:
                    self.punishments[str(msg.guild.id)][str(userid)] = 0
                self.punishments[str(msg.guild.id)][str(
                    userid)] = self.punishments[str(msg.guild.id)][str(userid)]+1
                punish = self.punishments[str(msg.guild.id)][str(userid)]
                await msg.channel.send('Spamは禁止されています')
                await self.save(msg.guild.id)
                for dmsg in self.sendmsgs[str(msg.guild.id)][str(msg.author.id)]:
                    try:
                        await dmsg.delete()
                    except:
                        str("メッセージが見つかりません")
                try:
                    memb = msg.author
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban'):
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban,'):
                            self.muteds[str(memb.guild.id)
                                        ][str(memb.id)] = dict()
                            self.muteds[str(memb.guild.id)][str(memb.id)]["time"] = int(time.time(
                            )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('ban,', ''))
                            self.muteds[str(memb.guild.id)][str(
                                memb.id)]["type"] = "ban"
                        await msg.author.ban()
                    if self.settings[str(msg.guild.id)]['action'][str(punish)] == 'kick':
                        await msg.author.kick()
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute'):
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute,'):
                            self.muteds[str(memb.guild.id)
                                        ][str(memb.id)] = dict()
                            self.muteds[str(memb.guild.id)][str(memb.id)]["time"] = int(time.time(
                            )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('mute,', ''))
                            self.muteds[str(memb.guild.id)][str(
                                memb.id)]["type"] = "mute"
                        await msg.author.add_roles(msg.guild.get_role(self.settings[str(memb.guild.id)]["muterole"]))
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('timeout'):
                        await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('timeout,', ''))), reason="sakura automod")
                except KeyError:
                    str('keyerror')
        else:
            self.sendtime[str(msg.guild.id)][str(msg.author.id)] = time.time()
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)] = [msg]
            self.sendcont[str(msg.guild.id)][str(msg.author.id)] = msg.content
        if not "ngword" in self.settings[str(msg.guild.id)]:
            self.settings[str(msg.guild.id)]["ngword"] = list()
        for nw in self.settings[str(msg.guild.id)]["ngword"]:
            if msg.content.find(nw) != -1:
                userid = msg.author.id
                if not str(msg.guild.id) in self.punishments:
                    self.punishments[str(msg.guild.id)] = dict()
                if not str(userid) in self.punishments[str(msg.guild.id)]:
                    self.punishments[str(msg.guild.id)][str(userid)] = 0
                self.punishments[str(msg.guild.id)][str(
                    userid)] = self.punishments[str(msg.guild.id)][str(userid)]+1
                punish = self.punishments[str(msg.guild.id)][str(userid)]
                await msg.channel.send('禁止ワードが含まれています')
                await self.save(msg.guild.id)
                await msg.delete()
                try:
                    memb = msg.author
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban'):
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('ban,'):
                            self.muteds[str(memb.guild.id)
                                        ][str(memb.id)] = dict()
                            self.muteds[str(memb.guild.id)][str(memb.id)]["time"] = int(time.time(
                            )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('ban,', ''))
                            self.muteds[str(memb.guild.id)][str(
                                memb.id)]["type"] = "ban"
                        await msg.author.ban()
                    if self.settings[str(msg.guild.id)]['action'][str(punish)] == 'kick':
                        await msg.author.kick()
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute'):
                        if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('mute,'):
                            self.muteds[str(memb.guild.id)
                                        ][str(memb.id)] = dict()
                            self.muteds[str(memb.guild.id)][str(memb.id)]["time"] = int(time.time(
                            )) + int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('mute,', ''))
                            self.muteds[str(memb.guild.id)][str(
                                memb.id)]["type"] = "mute"
                        await msg.author.add_roles(msg.guild.get_role(self.settings[str(memb.guild.id)]["muterole"]))
                    if self.settings[str(msg.guild.id)]['action'][str(punish)].startswith('timeout'):
                        await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(punish)].replace('timeout,', ''))), reason="sakura automod")
                except KeyError:
                    str('keyerror')

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx):
        guildid = str(ctx.guild.id)
        embed = discord.Embed(title='Settings', color=self.bot.Color)
        puni = ''
        try:
            for k in self.settings[guildid]['action'].keys():
                puni = puni+str(k)+':'+self.settings[guildid]['action'][k]+'\n'
        except KeyError:
            puni = 'No Punishment'
        ign = ''
        igchi = 0
        try:
            for igk in self.settings[str(guildid)]['ch']:
                igchi = igchi+1
                ign = ign+'<#'+str(igk)+'> is ignored\n'
        except KeyError:
            str('keyerror settings 0')
        try:
            for igkr in self.settings[str(guildid)]['role']:
                ign = ign+'<@&'+str(igkr)+'> is ignored\n'
                igchi = igchi+1
        except KeyError:
            str('keyerror settings 1')
        if igchi == 0:
            ign = 'No ignored'
        automod = ''
        try:
            automod = 'anti token:'+self.settings[str(guildid)]['tokens']+'\n'
        except KeyError:
            automod = 'anti token:off\n'
        try:
            automod = automod+'antiraid:'+self.settings[str(guildid)]['antiraid']+'、'+str(self.settings[str(
                guildid)]['raidcount'])+'人連続参加で動作、action:'+self.settings[str(guildid)]['raidaction']
        except KeyError:
            automod = automod+'antiraid:off'
        embed.add_field(name='punishments', value=puni)
        embed.add_field(name='ignore', value=ign)
        embed.add_field(name='automod settings', value=automod)
        alm = discord.AllowedMentions.none()
        nwo = ""
        try:
            for nw in self.settings[str(ctx.guild.id)]["ngword"]:
                nwo = nwo + nw + "\n"
        except KeyError:
            str("no ng word")
        ngembed = discord.Embed(
            title='NG Words', color=self.bot.Color, description=nwo)
        await ctx.send(embeds=[embed, ngembed], allowed_mentions=alm)

    @commands.command()
    async def addadminrole(self, ctx, role: discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
            self.settings[str(ctx.guild.id)]['adminrole'] = list()
        if role.id in self.settings[str(ctx.guild.id)]['adminrole']:
            await ctx.send('このロールはすでに追加されています')
        else:
            self.settings[str(ctx.guild.id)]['adminrole'].append(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('追加完了しました')

    @commands.command()
    async def addmodrole(self, ctx, role: discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = {"modrole": []}
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["modrole"] = list()
        if role.id in self.settings[str(ctx.guild.id)]['modrole']:
            await ctx.send('このロールはすでに追加されています')
        else:
            self.settings[str(ctx.guild.id)]['modrole'].append(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('追加完了しました')

    @commands.command()
    async def removeadminrole(self, ctx, role: discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = {"adminrole": []}
        if role.id in self.settings[str(ctx.guild.id)]['adminrole']:
            self.settings[str(ctx.guild.id)]['adminrole'].remove(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('削除完了しました')
        else:
            await ctx.send('このロールは追加されていません')

    @commands.command()
    async def removemodrole(self, ctx, role: discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        await self.check_permissions("admin", ctx)
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["modrole"] = list()
        if role.id in self.settings[str(ctx.guild.id)]['modrole']:
            self.settings[str(ctx.guild.id)]['modrole'].remove(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('削除完了しました')
        else:
            await ctx.send('このロールは追加されていません')

    def raise_missing_parms(self, ctx: commands.Context, permissions: list) -> None:
        "権限が足りないことを表すエラーを創出します。"
        raise commands.MissingPermissions(ctx, permissions)

    async def save(self, gid):
        if not str(gid) in self.settings:
            self.settings[str(gid)] = dict()
        if not str(gid) in self.muteds:
            self.muteds[str(gid)] = dict()
        if not str(gid) in self.punishments:
            self.punishments[str(gid)] = dict()
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from `automod` where `gid`=%s", (gid))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `automod` (`gid`, `setting`, `strike`, `muteds`) VALUES (%s, %s, %s, %s);", (gid, dumps(self.settings[str(gid)]), dumps(self.punishments[str(gid)]), dumps(self.muteds[str(gid)])))
                else:
                    await cur.execute("UPDATE `automod` SET `gid` = %s, `setting` = %s, `strike` = %s, `muteds` = %s WHERE (`gid` = %s);", (gid, dumps(self.settings[str(gid)]), dumps(self.punishments[str(gid)]), dumps(self.muteds[str(gid)]), gid))
                await conn.commit()


async def setup(bot: Bot):
    await bot.add_cog(AutoMod(bot))
