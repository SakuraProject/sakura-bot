from discord.ext import commands, tasks
import discord
from pytimeparse.timeparse import timeparse
from datetime import timedelta
from ujson import loads,dumps
import time
import re

def arrayinarray(list1,list2):
   for l1 in list1:
      if l1 in list2:
         return True
   return False

class automod(commands.Cog): 

    def __init__(self, bot): 
        self.bot = bot
        self.settings = dict()
        self.punishments = dict()
        self.muteds = dict()
        self.m=dict()
        self.time_=dict()
        self.sendtime=dict()
        self.sendcont=dict()
        self.sendmsgs=dict()
        self.untask.start()

    async def cog_load(self):
        ctsql = "CREATE TABLE if not exists `automod` (`gid` BIGINT NOT NULL,`setting` JSON NOT NULL,`strike` JSON NOT NULL,`muteds` JSON NOT NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)
                await cur.execute("SELECT * FROM `automod`")
                res = await cur.fetchall()
                for row in res:
                    self.settings[str(row[0])] = loads(row[1])
                    self.punishments[str(row[0])] = loads(row[2])
                    self.muteds[str(row[0])] = loads(row[3])


    @tasks.loop(seconds=10)
    async def untask(self):
        now = int(time.time())
        for gid in self.muteds.keys():
            g = self.bot.get_guild(int(gid))
            for uid in self.muteds[gid].keys():
                if int(self.muteds[gid][uid]["time"]) < now:
                    if self.muteds[gid][uid]["type"] == "ban":
                        member = await self.bot.fetch_user(int(uid))
                        await ctx.guild.unban(member)
                    elif self.muteds[gid][uid]["type"] == "mute":
                        member = g.get_member(int(uid))
                        await member.remove_roles(g.get_role(self.settings[str(gid)]["muterole"]))
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def timeout(self, ctx, member:discord.Member, *,time):
        sec = timeparse(sec)
        tdl = timedelta(seconds=sec)
        await member.timeout(tdl,reason="timeout command")
        await ctx.send("Ok")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def untimeout(self, ctx, member:discord.Member):
        await member.timeout(None,reason="untimeout command")
        await ctx.send("Ok")

    @commands.command()
    async def muterolesetup(self, ctx, role:discord.Role = None):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if role == None:
            role = await ctx.guild.create_role(name="sakura Muted",color=self.bot.Color)
        for tc in ctx.guild.text_channels:
            overwrite = tc.overwrites_for(role)
            overwrite.update(**{"send_messages":False,"add_reactions":False,"create_public_threads":False,"send_messages_in_threads":False})
            overwrites = tc.overwrites
            overwrites[role] = overwrite
            await tc.edit(overwrites=overwrites)
        for tc in ctx.guild.voice_channels:
            overwrite = tc.overwrites_for(role)
            overwrite.update(**{"send_messages":False,"add_reactions":False,"connect":False,"speak":False})
            overwrites = tc.overwrites
            overwrites[role] = overwrite
            await tc.edit(overwrites=overwrites)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        self.settings[str(ctx.guild.id)]["muterole"] = role.id
        await self.save(ctx.guild.id)
        await ctx.send("Ok")

    @commands.Cog.listener()
    async def on_guild_channel_create(self,channel):
        try:
            role = channel.guild.get_role(int(self.settings[str(channel.guild.id)]["muterole"]))
            overwrite = channel.overwrites_for(role)
            overwrite.update(**{"send_messages":False,"add_reactions":False,"create_public_threads":False,"send_messages_in_threads":False,"connect":False,"speak":False})
            overwrites = channel.overwrites
            overwrites[role] = overwrite
            await channel.edit(overwrites=overwrites)
        except:
            str("error")
    def raidcheck(member):
        if not str(member.guild.id) in self.m:
            self.m[str(member.guild.id)]=list()
        if not str(member.guild.id) in self.time_:
            self.time_[str(member.guild.id)]=time.time()
        self.m[str(member.guild.id)].append(member)
        if time.time() - self.time_[str(member.guild.id)] >=15.0:
            self.time_[str(member.guild.id)] =time.time()
            if time.time() - self.time_[str(member.guild.id)] >=60.0:
                self.m[str(member.guild.id)]=list()
        else:
            if len(self.m[str(member.guild.id)])>=int(self.settings[str(member.guild.id)]['raidcount']) and time.time() - self.time_[str(member.guild.id)] <=15.0:
                return True
            else:
                return False

    @commands.Cog.listener()
    async def on_member_join(self,member):
        if self.settings[str(member.guild.id)]['antiraid']=='on':
            if self.raidcheck(member):
                if self.settings[str(member.guild.id)]['raidaction']=='ban':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.ban(reason="sakura anti raid")
                if self.settings[str(member.guild.id)]['raidaction']=='kick':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.kick(reason="sakura anti raid")
                if self.settings[str(member.guild.id)]['raidaction']=='mute':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.add_roles(int(member.guild.get_role(self.settings[str(member.guild.id)]["muterole"])),reason="sakura anti raid")
                        if not str(member.guild.id) in self.muteds:
                            self.muteds[str(member.guild.id)] = dict()
                        if self.settings[str(member.guild.id)]['raidactiontime'] != None:
                            self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(member.guild.id)]['raidactiontime'])
                            self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "mute"
                    await self.save(member.guild.id)
                if self.settings[str(member.guild.id)]['raidaction']=='timeout':
                    for memb in self.m[str(member.guild.id)]:
                        await memb.timeout(timedelta(seconds=int(self.settings[str(member.guild.id)]['raidactiontime'])),reason="sakura anti raid")

    @commands.group()
    async def ngword(self,ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @ngword.command()
    async def set(self,ctx,*,word):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not "ngword" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["ngword"] = list()
        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            await ctx.send("すでに設定されています")
        else:
            self.settings[str(ctx.guild.id)]["ngword"].append(word)
            await ctx.send("設定しました")
            await self.save(ctx.guild.id)

    @ngword.command()
    async def remove(self,ctx,*,word):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not "ngword" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["ngword"] = list()
        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            self.settings[str(ctx.guild.id)]["ngword"].pop(word)
            await ctx.send("削除しました")
            await self.save(ctx.guild.id)
        else:
            await ctx.send("設定されていません")

    @commands.command()
    async def antiraid(self,ctx,joincount:int,action='kick',time=None):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if time != None:
            time = timeparse(time)
        if action == 'kick':
            self.settings[str(ctx.guild.id)].update({"antiraid":"on","raidcount":joincount,"raidaction":action})
            await ctx.send("設定をonにしました")

        if action == 'ban':
            self.settings[str(ctx.guild.id)].update({"antiraid":"on","raidcount":joincount,"raidaction":action,'raidactiontime':time})
            await ctx.send("設定をonにしました")

        if action == 'mute':
            self.settings[str(ctx.guild.id)].update({"antiraid":"on","raidcount":joincount,"raidaction":action,'raidactiontime':time})
            await ctx.send("設定をonにしました")
        if action == 'timeout':
            self.settings[str(ctx.guild.id)].update({"antiraid":"on","raidcount":joincount,"raidaction":action,'raidactiontime':time})
            await ctx.send("設定をonにしました")
        if action == 'none':
            self.settings[str(ctx.guild.id)].update({"antiraid":"off","raidcount":joincount,"raidaction":action})
            await ctx.send("設定をoffにしました")
        await self.save(ctx.guild.id)

    @commands.command()
    async def ignore(self, ctx, id:int = 0):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
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

    def ig(self,msg):
        if not str(msg.guild.id) in self.settings:
            self.settings[str(msg.guild.id)]=dict()
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
    async def antitokens(self,ctx,onoff):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if onoff == 'on':
            self.settings[str(ctx.guild.id)]['tokens']='on'
            await self.save(ctx.guild.id)
            await ctx.send('antitokenモードをonにしました')
        if onoff == 'off':
            self.settings[str(ctx.guild.id)]['tokens']='off'
            await self.save(ctx.guild.id)
            await ctx.send('antitokenモードをoffにしました')

    @commands.command()
    async def punishment(self,ctx,strike,modaction,sec=None):
        if sec != None:
            sec = timeparse(sec)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole']=list()
        if not (ctx.author.guild_permissions.manage_guild or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole']) or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['modrole'])):
            await no_manserver_perm(ctx)
            return
        stri=int(strike)
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "action" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['action']=dict()
        if modaction=='ban' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='ban,'+str(int(sec))
        elif modaction=='ban':
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='ban'
        if modaction=='mute' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='mute,'+str(int(sec))
        elif modaction=='mute':
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='mute'
        if modaction=='kick':
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='kick'
        if modaction=='timeout' and sec != None:
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='timeout,'+str(int(sec))
        if modaction=='none':
            self.settings[str(ctx.guild.id)]['action'][str(stri)]='None'
        await self.save(ctx.guild.id)
        await ctx.send(str(stri)+'に'+str(modaction)+'を設定しました')

    @commands.command()
    async def antispam(self,ctx,spamcount:int):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        self.settings[str(ctx.guild.id)]['duplct']=spamcount
        await self.save(ctx.guild.id)
        await ctx.send(str(spamcount)+'回連投で1Strike付与します')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def pardon(self,ctx,id:int,strikes=1):
        self.punishments[str(ctx.guild.id)][str(id)]=self.punishments[str(ctx.guild.id)][str(id)]-strikes
        await ctx.send("pardoned "+str(strikes)+"strikes on"+str(id))
        await self.save(ctx.guild.id)
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def check(self,ctx,id:int):
        await ctx.send(str(id)+"has"+str(self.punishments[str(ctx.guild.id)][str(id)])+"strikes")
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self,ctx,id:int):
        member = await self.bot.fetch_user(id)
        await ctx.guild.unban(member)
        await ctx.send("banを解除しました")
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self,ctx,member:discord.Member):
        await member.kick()
        await ctx.send("kickしました")
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self,ctx,id:int):
        member = await self.bot.fetch_user(id)
        await ctx.guild.ban(member)
        await ctx.send("banしました")
    @commands.command()
    async def mute(self,ctx,member:discord.Member):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole']=list()
        if not (ctx.author.guild_permissions.manage_guild or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole']) or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['modrole'])):
            await no_manserver_perm(ctx)
            return
        await member.add_roles(ctx.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
        await ctx.send("muteしました")
    @commands.command()
    async def unmute(self,ctx,member:discord.Member):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]['modrole']=list()
        if not (ctx.author.guild_permissions.manage_guild or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole']) or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['modrole'])):
            await no_manserver_perm(ctx)
            return
        await member.remove_roles(ctx.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
        await ctx.send("unmuteしました")

    @commands.Cog.listener()
    async def on_message(self,msg):
        if msg.author.id == self.bot.user.id:
            return
        try:
            if self.settings[str(msg.guild.id)]['tokens'] =='on':
                tkreg=r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'
                if re.search(tkreg,msg.content) != None:
                    userid=msg.author.id
                    guildid=msg.guild.id
                    if not str(ctx.guild.id) in self.punishments:
                        self.punishments[str(ctx.guild.id)]=dict()
                    if str(userid) in self.punishments[str(msg.guild.id)]:
                        self.punishments[str(msg.guild.id)][str(userid)]=0
                    self.punishments[str(msg.guild.id)][str(userid)]=self.punishments[str(msg.guild.id)][str(userid)]+1
                    await msg.delete()
                    await msg.channel.send("tokenの送信はこのサーバーで禁止されています")
                    userid=msg.author.id
                    try:
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='ban':
                            if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                                self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                                self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('ban,',''))
                                self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "ban"
                            await msg.author.ban()
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='kick':
                            await msg.author.kick()
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute'):
                            if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                                self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                                self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('mute,',''))
                                self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "mute"
                            await msg.author.add_roles(msg.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('timeout'):
                            await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('timeout,',''))),reason="sakura automod")
                    except KeyError:
                        str('keyerror')
                    await self.save(msg.guild.id)
        except KeyError:
            str('KeyError')
        if self.ig(msg):
            return
        try:
            str(self.sendcont[str(msg.guild.id)])
        except:
            self.sendcont[str(msg.guild.id)]=dict()
        try:
            str(self.sendcont[str(msg.guild.id)][str(msg.author.id)])
        except:
            self.sendcont[str(msg.guild.id)][str(msg.author.id)]=''
        try:
            len(self.sendmsgs[str(msg.guild.id)])
        except:
            self.sendmsgs[str(msg.guild.id)]=dict()
        try:
            len(self.sendmsgs[str(msg.guild.id)][str(msg.author.id)])
        except:
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)]=list()
        try:
            len(self.sendtime[str(msg.guild.id)])
        except:
            self.sendtime[str(msg.guild.id)]=dict()
        try:
            str(self.sendtime[str(msg.guild.id)][str(msg.author.id)])
        except:
            self.sendtime[str(msg.guild.id)][str(msg.author.id)]=time.time()
        if time.time()-self.sendtime[str(msg.guild.id)][str(msg.author.id)]<=5.0:
            self.sendtime[str(msg.guild.id)][str(msg.author.id)]=time.time()
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)].append(msg)
            if not str(msg.guild.id) in self.settings:
                self.settings[str(msg.guild.id)]=dict()
            if not 'duplct' in self.settings[str(msg.guild.id)]:
                self.settings[str(msg.guild.id)]['duplct']=5
            if len(self.sendmsgs[str(msg.guild.id)][str(msg.author.id)])>=int(self.settings[str(msg.guild.id)]['duplct']):
                userid=msg.author.id
                guildid=msg.guild.id
                if not str(ctx.guild.id) in self.punishments:
                    self.punishments[str(ctx.guild.id)]=dict()
                if str(userid) in self.punishments[str(msg.guild.id)]:
                    self.punishments[str(msg.guild.id)][str(userid)]=0
                self.punishments[str(msg.guild.id)][str(userid)]=self.punishments[str(msg.guild.id)][str(userid)]+1
                await msg.channel.send('Spamは禁止されています')
                await self.save(msg.guild.id)
                for dmsg in self.sendmsgs[str(msg.guild.id)][str(msg.author.id)]:
                    await dmsg.delete()
                try:
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='ban':
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                            self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('ban,',''))
                            self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "ban"
                        await msg.author.ban()
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='kick':
                        await msg.author.kick()
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute'):
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                            self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('mute,',''))
                            self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "mute"
                        await msg.author.add_roles(msg.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('timeout'):
                        await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('timeout,',''))),reason="sakura automod")
                except KeyError:
                    str('keyerror')
        else:
            self.sendtime[str(msg.guild.id)][str(msg.author.id)]=time.time()
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)]=list()
            self.sendmsgs[str(msg.guild.id)][str(msg.author.id)].append(msg)
            self.sendcont[str(msg.guild.id)][str(msg.author.id)]=msg.content
        if not "ngword" in self.settings[str(msg.guild.id)]:
            self.settings[str(msg.guild.id)]["ngword"]=list()
        for nw in self.settings[str(msg.guild.id)]["ngword"]:
            if msg.content.find(nw) != -1:
                try:
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='ban':
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                            self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('ban,',''))
                            self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "ban"
                        await msg.author.ban()
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])]=='kick':
                        await msg.author.kick()
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute'):
                        if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('mute,'):
                            self.muteds[str(member.guild.id)][str(memb.id)] = dict()
                            self.muteds[str(member.guild.id)][str(memb.id)]["time"] = int(time.time()) + int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('mute,',''))
                            self.muteds[str(member.guild.id)][str(memb.id)]["type"] = "mute"
                        await msg.author.add_roles(msg.guild.get_role(self.settings[str(member.guild.id)]["muterole"]))
                    if self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].startswith('timeout'):
                        await msg.author.timeout(timedelta(seconds=int(self.settings[str(msg.guild.id)]['action'][str(self.punishments[str(msg.guild.id)][str(userid)])].replace('timeout,',''))),reason="sakura automod")
                except KeyError:
                    str('keyerror')

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def settings(self,ctx):
        guildid=str(ctx.guild.id)
        embed=discord.Embed(title='Settings',color=self.bot.Color)
        puni=''
        try:
            for k in self.settings[guildid]['action'].keys():
                puni=puni+str(k)+':'+self.settings[guildid]['action'][k]+'\n'
        except KeyError:
            puni='No Punishment'
        ign=''
        igchi=0
        try:
            for igk in self.settings[str(guildid)]['ch']:
                igchi=igchi+1
                ign=ign+'<#'+str(igk)+'> is ignored\n'
        except KeyError:
            str('keyerror settings 0')
        try:
            for igkr in self.settings[str(guildid)]['role']:
                ign=ign+'<@&'+str(igkr)+'> is ignored\n'
                igchi=igchi+1
        except KeyError:
            str('keyerror settings 1')
        if igchi ==0:
            ign='No ignored'
        automod=''
        try:
            automod='anti token:'+self.settings[str(guildid)]['tokens']+'\n'
        except KeyError:
            automod='anti token:off\n'
        try:
            automod=automod+'antiraid:'+self.settings[str(guildid)]['antiraid']+'、'+str(self.settings[str(guildid)]['raidcount'])+'人連続参加で動作、action:'+self.settings[str(guildid)]['raidaction']
        except KeyError:
            automod=automod+'antiraid:off'
        embed.add_field(name='punishments',value=puni)
        embed.add_field(name='ignore',value=ign)
        embed.add_field(name='automod settings',value=automod)
        alm = discord.AllowedMentions.none()
        nwo = ""
        try:
            for nw in self.settings[str(ctx.guild.id)]["ngword"]:
                nwo = nwo + nw + "\n"
        except KeyError:
            str("no ng word")
        ngembed=discord.Embed(title='NG Words',color=self.bot.Color,description=nwo)
        await ctx.send(embeds=[embed,ngembed],allowed_mentions=alm)

    @commands.command()
    async def addadminrole(ctx,role:discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
            self.settings[str(ctx.guild.id)]['adminrole']=list()
        if role.id in self.settings[str(ctx.guild.id)]['adminrole']:
            await ctx.send('このロールはすでに追加されています')
        else:
            self.settings[str(ctx.guild.id)]['adminrole'].append(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('追加完了しました')
    @commands.command()
    async def addmodrole(ctx,role:discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
            self.settings[str(ctx.guild.id)]['modrole']=list()
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["modrole"] = list()
        if role.id in self.settings[str(ctx.guild.id)]['modrole']:
            await ctx.send('このロールはすでに追加されています')
        else:
            self.settings[str(ctx.guild.id)]['modrole'].append(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('追加完了しました')
    @commands.command()
    async def removeadminrole(ctx,role:discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
            self.settings[str(ctx.guild.id)]['adminrole']=list()
        if role.id in self.settings[str(ctx.guild.id)]['adminrole']:
            self.settings[str(ctx.guild.id)]['adminrole'].remove(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('削除完了しました')
        else:
            await ctx.send('このロールは追加されていません')
    @commands.command()
    async def removemodrole(ctx,role:discord.Role):
        if not str(ctx.guild.id) in self.settings:
            self.settings[str(ctx.guild.id)] = dict()
        if not "adminrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["adminrole"] = list()
        if not (ctx.author.guild_permissions.administrator or arrayinarray([r.id for r in ctx.author.roles],self.settings[str(ctx.guild.id)]['adminrole'])):
            await self.no_admin_perm(ctx)
            return
        if not "modrole" in self.settings[str(ctx.guild.id)]:
            self.settings[str(ctx.guild.id)]["modrole"] = list()
        if role.id in self.settings[str(ctx.guild.id)]['modrole']:
            self.settings[str(ctx.guild.id)]['modrole'].remove(role.id)
            await self.save(ctx.guild.id)
            await ctx.send('削除完了しました')
        else:
            await ctx.send('このロールは追加されていません')

    async def no_admin_perm(self,ctx):
        """
        admin roleがなく、権限がないときに通常のdiscordと同じエラーを発生させます
        """
        raise discord.ext.commands.MissingPermissions(["administrator"])

    async def save(self,gid):
        if not str(gid) in self.settings:
            self.settings[str(gid)] = dict()
        if not str(gid) in self.muteds:
            self.muteds[str(gid)] = dict()
        if not str(gid) in self.punishments:
            self.punishments[str(gid)] = dict()
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from `automod` where `gid`=%s",(gid))
                res = await cur.fetchall()
                await conn.commit()
                if len(res) == 0:
                    await cur.execute("INSERT INTO `automod` (`gid`, `setting`, `strike`, `muteds`) VALUES (%s, %s, %s, %s);",(gid,dumps(self.settings[str(gid)]),dumps(self.punishments[str(gid)]),dumps(self.muteds[str(gid)])))
                else:
                    await cur.execute("UPDATE `automod` SET `gid` = %s, `setting` = %s, `strike` = %s, `muteds` = %s WHERE (`gid` = %s);",(gid,dumps(self.settings[str(gid)]),dumps(self.punishments[str(gid)]),dumps(self.muteds[str(gid)]),gid))
                await conn.commit()

async def setup(bot):
    await bot.add_cog(automod(bot))
