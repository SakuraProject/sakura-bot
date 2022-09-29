"""New Automod
新AutoModシステム。
"""

from typing import Literal

from copy import deepcopy

from discord.ext import commands, tasks
import discord
from pytimeparse.timeparse import timeparse
from datetime import timedelta
from orjson import loads, dumps as dumps_default
import time
import re

from utils import Bot, TryConverter

from ._types import Setting, Actions, MutedUser


def dumps(*args, **kwargs):
    return dumps_default(*args, **kwargs).decode()


def arrayinarray(list1, list2) -> bool:
    "list1の項目がlist2の中に一つでも含まれているかをチェックします。"
    return any(item in list2 for item in list1)


class AutoMod(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings: dict[str, Setting] = {}
        self.punishments: dict[str, dict[str, int]] = {}  # skrike数
        self.muteds: dict[str, dict[str, MutedUser]] = {}  # ミュート情報
        self.m: dict[str, list[discord.Member]] = {}  # raid関連
        self.time_ = {}  # raid関連
        self.sendtime: dict[str, dict[str, float]] = {}  # spam対策関連
        self.sendcont: dict[str, dict[str, str]] = {}  # spam対策関連
        self.sendmsgs: dict[str,
                            dict[str, list[discord.Message]]] = {}  # spam対策関連
        self.sendcount: dict[str, dict[str, str]] = {}  # spam対策関連
        self.untask.start()

    async def cog_load(self):
        sql_stmt = """CREATE TABLE if not exists AutoModSetting (
            GuildId BIGINT PRIMARY KEY NOT NULL,
            AdminRole JSON,
            ModRole JSON,
            MuteRole BIGINT,
            AntiRaid VARCHAR(5),
            RaidAction VARCHAR(15),
            RaidActionTime MEDIUMINT UNSIGNED,
            RaidCount MEDIUMINT UNSIGNED,
            IgnoreChannel JSON,
            IgnoreRole JSON,
            NGWord JSON,
            Duplct TINYINT UNSIGNED,
            Action JSON,
            Tokens VARCHAR(5)
        ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"""
        sql_stmt2 = """CREATE TABLE IF NOT EXISTS AutoModPunishments (
            GuildId BIGINT NOT NULL,
            MemberId BIGINT NOT NULL,
            Strike INT,
            PRIMARY KEY(GuildId, MemberId)
        );"""

        async def sqling(cursor):
            await cursor.execute(sql_stmt)
            await cursor.execute("SELECT * FROM AutoModSetting")
            r1 = await cursor.fetchall()
            await cursor.execute(sql_stmt2)
            await cursor.execute("SELECT * FROM AutoModPunishments")
            return (r1, await cursor.fetchall())

        res = await self.bot.execute_sql(sqling)
        assert isinstance(res, tuple) and isinstance(res[0], tuple)

        for row in res[0]:
            self.settings[str(row[0])] = Setting(
                adminrole=loads(row[1]), modrole=loads(row[2]),
                muterole=row[3], antiraid=row[4], raidaction=row[5],
                raidactiontime=row[6], raidcount=row[7],
                ignore_channel=loads(row[8]), ignore_role=loads(row[9]),
                ngword=loads(row[10]), duplct=row[11], action=loads(row[12]),
                tokens=row[13]
            )
        for row in res[1]:
            self.punishments.setdefault(str(row[0]), {})
            self.punishments[str(row[0])][str(row[1])] = row[2]

    def data_check(self, guild_id: int, author_id: int = 0) -> None:
        defaults = Setting(
            adminrole=[], modrole=[],
            muterole=0, antiraid="off",
            raidaction="none", raidactiontime=0,
            raidcount=0, ignore_channel=[],
            ignore_role=[], ngword=[],
            duplct=0, action={}, tokens="on"
        )
        if str(guild_id) not in self.settings:
            self.settings[str(guild_id)] = defaults
        for key, value in defaults.items():
            if key not in self.settings[str(guild_id)]:
                self.settings[str(guild_id)][key] = value
        self.settings[str(guild_id)] = Setting(
            **self.settings[str(guild_id)])  # type: ignore

        # デフォルトの設定
        for item in (
            self.sendmsgs, self.sendtime,
            self.sendcont, self.sendcount, self.punishments
        ):
            item.setdefault(str(guild_id), {})  # type: ignore
        if author_id:
            self.sendmsgs[str(guild_id)].setdefault(str(author_id), [])
            self.sendtime[str(guild_id)].setdefault(
                str(author_id), time.time())
            self.sendcont[str(guild_id)].setdefault(str(author_id), '')
            self.sendcount[str(guild_id)].setdefault(str(author_id), '')
            self.punishments[str(guild_id)].setdefault(str(author_id), 0)

    @commands.hybrid_group()
    @commands.guild_only()
    async def automod(self, ctx: commands.Context):
        if ctx.invoked_subcommand:
            return
        await ctx.send("使い方が違います。")

    async def check_permissions(
        self, type_: Literal["admin", "manage-guild"], ctx: commands.Context
    ) -> None:
        "ctx.authorが特定のtypeの権限を持っているか確認します。持っていなければエラーを送出します。"
        assert ctx.guild is not None
        assert isinstance(ctx.author, discord.Member)
        self.data_check(ctx.guild.id)

        if type_ == "admin" and not (
            ctx.author.guild_permissions.administrator
            or arrayinarray(
                [r.id for r in ctx.author.roles],
                self.settings[str(ctx.guild.id)]['adminrole']
            )
        ):
            raise commands.MissingPermissions(["administrator"])
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
            raise commands.MissingPermissions(["manage_guild"])

    @tasks.loop(seconds=10)
    async def untask(self):
        # Unban / unmute用のループ。
        now = int(time.time())
        for gid in self.muteds:
            g = self.bot.get_guild(int(gid))
            if not g:
                del self.muteds[gid]
                continue
            for uid in self.muteds[gid].keys():
                if int(self.muteds[gid][uid].get("time", 0)) < now:
                    try:
                        if self.muteds[gid][uid]["type"] == "ban":
                            member = discord.Object(int(uid))
                            await g.unban(member)
                        elif self.muteds[gid][uid]["type"] == "mute":
                            member = g.get_member(int(uid))
                            if not member:
                                del self.muteds[gid][uid]
                                continue
                            await member.remove_roles(discord.Object(self.settings[str(gid)]["muterole"]))
                    except BaseException:
                        pass

    @automod.command()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def muterolesetup(self, ctx: commands.Context, role: discord.Role | None = None):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        if role is None:
            role = discord.utils.get(ctx.guild.roles, name="sakura Muted")
            if role is None:
                role = await ctx.guild.create_role(
                    name="sakura Muted", color=self.bot.Color
                )
        exceptions = []

        for channel in ctx.guild.text_channels:
            overwrite = channel.overwrites_for(role)
            overwrite.update(**{"send_messages": False, "add_reactions": False,
                             "create_public_threads": False, "send_messages_in_threads": False})
            overwrites = channel.overwrites
            overwrites[role] = overwrite
            try:
                await channel.edit(overwrites=overwrites)
            except discord.Forbidden:
                exceptions.append(channel.mention)

        for tc in ctx.guild.voice_channels:
            overwrite = tc.overwrites_for(role)
            overwrite.update(
                **{"send_messages": False, "add_reactions": False, "connect": False, "speak": False})
            overwrites = tc.overwrites
            overwrites[role] = overwrite
            try:
                await tc.edit(overwrites=overwrites)
            except discord.Forbidden:
                exceptions.append(tc.mention)

        self.settings[str(ctx.guild.id)]["muterole"] = role.id
        await self.save(ctx.guild.id)
        await ctx.send("Ok")

    @commands.Cog.listener()
    async def on_guild_channel_create(
        self, channel: discord.TextChannel | discord.VoiceChannel
        | discord.ForumChannel | discord.CategoryChannel | discord.StageChannel
    ):
        role = channel.guild.get_role(
            int(self.settings[str(channel.guild.id)]["muterole"]))
        if not role:
            return

        overwrite = channel.overwrites_for(role)
        overwrite.update(**{"send_messages": False, "add_reactions": False, "create_public_threads": False,
                            "send_messages_in_threads": False, "connect": False, "speak": False})
        overwrites = channel.overwrites
        overwrites[role] = overwrite
        try:
            await channel.edit(overwrites=overwrites)
        except discord.Forbidden:
            pass

    def raidcheck(self, member):
        if str(member.guild.id) not in self.m:
            self.m[str(member.guild.id)] = []
        if str(member.guild.id) not in self.time_:
            self.time_[str(member.guild.id)] = time.time()
        self.m[str(member.guild.id)].append(member)
        if time.time() - self.time_[str(member.guild.id)] >= 15.0:
            self.time_[str(member.guild.id)] = time.time()
            if time.time() - self.time_[str(member.guild.id)] >= 60.0:
                self.m[str(member.guild.id)] = []
        elif (
            len(self.m[str(member.guild.id)]) >= int(
                self.settings[str(member.guild.id)]['raidcount']
            ) and time.time() - self.time_[str(member.guild.id)] <= 15.0
        ):
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        "antiraid用のイベント。"
        self.data_check(member.guild.id, member.id)

        if (
            not (g_setting := deepcopy(
                self.settings[str(member.guild.id)]))['antiraid']
            or g_setting['raidaction'] == "none"
            or self.raidcheck(member)
        ):
            return

        # do_punishで実行するために少し改造
        g_setting["action"][str(15 ** 12)] = g_setting["raidaction"]
        if g_setting["raidactiontime"] != "none":
            g_setting["action"][str(
                15 ** 12)] += f",{g_setting['raidactiontime']}"
        before = self.punishments[str(member.guild.id)].get(str(member.id), 0)
        self.punishments[str(member.guild.id)][str(member.id)] = 15 ** 12

        await self.do_punish(g_setting, member)

        self.punishments[str(member.guild.id)][str(member.id)] = before

    @automod.group()
    async def ngword(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @ngword.command()
    async def set(self, ctx: commands.Context, *, word):
        assert ctx.guild
        await self.check_permissions("admin", ctx)

        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            await ctx.send("すでに設定されています")
        else:
            self.settings[str(ctx.guild.id)]["ngword"].append(word)
            await ctx.send("設定しました")
            await self.save(ctx.guild.id)

    @ngword.command()
    async def remove(self, ctx: commands.Context, *, word: str):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        if word in self.settings[str(ctx.guild.id)]["ngword"]:
            self.settings[str(ctx.guild.id)]["ngword"].remove(word)
            await ctx.send("削除しました。")
            await self.save(ctx.guild.id)
        else:
            await ctx.send("その言葉は設定されていません。")

    @automod.command()
    async def antiraid(
        self, ctx: commands.Context, joincount: int,
        action: Actions = 'kick', time: str = ""
    ):
        assert ctx.guild
        await self.check_permissions("admin", ctx)

        self.settings[str(ctx.guild.id)
                      ]["raidactiontime"] = timeparse(time) or 0

        self.settings[str(ctx.guild.id)
                      ]["antiraid"] = "off" if action == "none" else "on"
        self.settings[str(ctx.guild.id)]["raidcount"] = joincount
        self.settings[str(ctx.guild.id)]["raidaction"] = action
        if action != "none":
            await ctx.send("設定をonにしました")
        else:
            await ctx.send("設定をoffにしました")
        await self.save(ctx.guild.id)

    @automod.command()
    async def ignore(
        self, ctx: commands.Context, mode: Literal["channel", "role"],
        target: TryConverter[discord.TextChannel,
                             discord.Role] = commands.CurrentChannel
    ):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        if mode == "channel":
            self.settings[str(ctx.guild.id)
                          ]["ignore_channel"].append(target.id)
        else:
            self.settings[str(ctx.guild.id)]["ignore_role"].append(target.id)

        await ctx.send("設定完了しました")
        await self.save(ctx.guild.id)

    def ig(self, msg: discord.Message) -> bool:
        assert msg.guild and isinstance(msg.author, discord.Member)
        self.data_check(msg.guild.id)

        if msg.channel.id in self.settings[str(
                msg.guild.id)]["ignore_channel"]:
            return True
        return arrayinarray(
            [r.id for r in msg.author.roles],
            self.settings[str(msg.guild.id)]["ignore_role"]
        )

    @automod.command()
    async def antitokens(self, ctx: commands.Context, onoff: bool):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        is_onoff = "on" if onoff else "off"
        self.settings[str(ctx.guild.id)]['tokens'] = is_onoff
        await self.save(ctx.guild.id)
        await ctx.send(f'antitokenモードを{is_onoff}にしました')

    @automod.command()
    async def punishment(
        self, ctx: commands.Context,
        strike: int, modaction: Actions, sec=None
    ):
        if modaction == "none" and sec:
            return await ctx.send("設定解除の場合に時間を指定することは出来ません！")
        if modaction == "kick" and sec:
            return await ctx.send("キックの場合に時間を指定することは出来ません！")
        if modaction == "timeout" and not sec:
            return await ctx.send("タイムアウトの場合は時間を指定しなければいけません！")
        await self.check_permissions("manage-guild", ctx)
        assert ctx.guild
        if sec is not None:
            sec2 = timeparse(sec)
        else:
            sec2 = None

        self.settings[str(ctx.guild.id)]["action"][str(strike)] = modaction
        if sec2 is not None:
            self.settings[str(ctx.guild.id)]["action"][str(
                strike)] += f",{sec2}"

        await self.save(ctx.guild.id)
        await ctx.send(f"{strike}ストライクで{modaction}をするように設定しました。")

    @automod.command()
    async def antispam(self, ctx: commands.Context, spamcount: int):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        self.settings[str(ctx.guild.id)]['duplct'] = spamcount
        await self.save(ctx.guild.id)
        await ctx.send(f"{spamcount}回連投で1Strike付与します")

    @automod.command()
    @commands.has_permissions(ban_members=True)
    async def pardon(
        self, ctx: commands.Context,
        target: TryConverter[discord.Member, discord.User, discord.Object],
        strikes=1
    ):
        await self.check_permissions("manage-guild", ctx)
        assert ctx.guild

        if not target.id in self.punishments[str(ctx.guild.id)]:
            return await ctx.send("ユーザーは処罰されたことがありません。")
        self.punishments[str(ctx.guild.id)][str(target.id)] -= strikes
        await ctx.send(f"pardoned {strikes}strikes on <@{target.id}>")
        await self.save(ctx.guild.id)

    @automod.command()
    async def check(
        self, ctx: commands.Context,
        user: TryConverter[discord.Member, discord.User, discord.Object]
    ):
        assert ctx.guild
        self.data_check(ctx.guild.id)

        g_punish = self.punishments[str(ctx.guild.id)]
        await ctx.send(
            f"<@{user.id}>は{g_punish.get(str(user.id), 0)}strikeです。"
        )

    @commands.command()
    @commands.guild_only()
    async def mute(self, ctx: commands.Context, member: discord.Member):
        await self.check_permissions("manage-guild", ctx)

        await member.add_roles(
            discord.Object(self.settings[str(member.guild.id)]["muterole"])
        )
        await ctx.send(f"{member.mention}をミュートしました。")

    @commands.command()
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        await self.check_permissions("manage-guild", ctx)

        await member.remove_roles(
            discord.Object(self.settings[str(member.guild.id)]["muterole"])
        )
        await ctx.send(f"{member.mention}をミュート解除しました。")

    async def do_punish(
        self, g_setting: Setting, author: discord.Member,
        channel: discord.TextChannel | discord.VoiceChannel | discord.Thread |
        discord.DMChannel | discord.PartialMessageable | discord.GroupChannel | None = None
    ):
        "刑罰を実行します。"
        punish = self.punishments[str(author.guild.id)][str(author.id)]
        if str(punish) not in g_setting["action"]:
            return
        try:
            if g_setting['action'][str(punish)].startswith('ban'):
                if g_setting['action'][str(punish)].startswith('ban,'):
                    self.muteds[str(author.guild.id)][str(author.id)] = MutedUser(
                        time=int(time.time()) +
                        int(g_setting['action'][str(punish)][4:]),
                        type="ban"
                    )
                await author.ban(reason="sakura automod")
            if g_setting['action'][str(punish)] == 'kick':
                await author.kick(reason="sakura automod")
            if g_setting['action'][str(punish)].startswith('mute'):
                if g_setting["muterole"]:
                    await author.add_roles(discord.Object(g_setting["muterole"]))
                    if g_setting['action'][str(punish)].startswith('mute,'):
                        self.muteds[str(author.guild.id)][str(author.id)] = MutedUser(
                            time=int(time.time()) +
                            int(g_setting["action"][str(punish)][5:]),
                            type="mute"
                        )
            if g_setting['action'][str(punish)].startswith('timeout'):
                await author.timeout(
                    timedelta(seconds=int(
                        g_setting['action'][str(punish)][8:])),
                    reason="sakura automod"
                )
        except discord.HTTPException:
            try:
                if not author.guild.owner:
                    return
                await (channel or author.guild.owner).send(
                    "⚠️ユーザーの処罰に失敗しました。権限を確認してください。"
                )
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild is None or msg.author == msg.guild.me:
            return

        assert isinstance(msg.author, discord.Member)
        gid, uid = msg.guild.id, msg.author.id

        self.data_check(gid, uid)

        s_gid, s_uid = str(gid), str(uid)
        g_setting = self.settings[s_gid]

        if g_setting['tokens'] == 'on':
            # トークン保護
            if re.search(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', msg.content):
                self.punishments[s_gid][s_uid] += 1
                await msg.channel.send("tokenの送信はこのサーバーで禁止されています")
                try:
                    await msg.delete()
                except discord.Forbidden:
                    await msg.channel.send(
                        "⚠️メッセージの削除に失敗しました。権限を確認してください。"
                    )
                await self.do_punish(g_setting, msg.author, msg.channel)

                await self.save(gid)

        if self.ig(msg):
            return

        if time.time() - self.sendtime[s_gid][s_uid] <= 2.0:
            # Spam対策
            self.sendtime[s_gid][s_uid] = time.time()
            self.sendmsgs[s_gid][s_uid].append(msg)
            if (len(self.sendmsgs[s_gid][s_uid]) >= int(g_setting['duplct'])
                    and int(g_setting['duplct']) != 0):
                self.punishments[s_gid][s_uid] += 1
                await msg.channel.send('Spamは禁止されています')
                await self.save(gid)
                try:
                    if isinstance(msg.channel, discord.TextChannel):
                        await msg.channel.purge(
                            check=lambda m: m in self.sendmsgs[s_gid][s_uid]
                        )
                    else:
                        for m in self.sendmsgs[s_gid][s_uid]:
                            await m.delete()
                except discord.Forbidden:
                    await msg.channel.send("⚠️削除に失敗しました。権限を確認してください。")
                await self.do_punish(g_setting, msg.author, msg.channel)
        else:
            self.sendtime[s_gid][s_uid] = time.time()
            self.sendmsgs[s_gid][s_uid] = [msg]
            self.sendcont[s_gid][s_uid] = msg.content

        for nw in g_setting["ngword"]:
            # NGワード
            if msg.content.find(nw) != -1:
                self.punishments[s_gid][s_uid] += 1
                await msg.channel.send('禁止ワードが含まれています')
                await self.save(gid)
                await msg.delete()
                await self.do_punish(g_setting, msg.author, msg.channel)

    @automod.command("settings")
    @commands.has_permissions(manage_guild=True)
    async def _settings(self, ctx: commands.Context):
        assert ctx.guild
        self.data_check(ctx.guild.id)

        g_setting = self.settings[str(ctx.guild.id)]
        embed = discord.Embed(title='Settings', color=self.bot.Color)
        puni = ''
        for k in g_setting['action'].keys():
            puni = puni + str(k) + ':' + g_setting['action'][k] + '\n'
        if puni == '':
            puni = 'No Punishments'
        ign = ''
        igchi = 0
        for igk in g_setting['ignore_channel']:
            igchi = igchi + 1
            ign = ign + '<#' + str(igk) + '> is ignored\n'
        for igkr in g_setting['ignore_role']:
            ign = ign + '<@&' + str(igkr) + '> is ignored\n'
            igchi = igchi + 1
        if igchi == 0:
            ign = 'No ignored'
        automod = 'anti token:' + g_setting['tokens'] + '\n'
        automod += (f"antiraid: {g_setting['antiraid']}、"
                    f"{g_setting['raidcount']}人連続参加で動作、action: {g_setting['raidaction']}")
        embed.add_field(name='punishments', value=puni)
        embed.add_field(name='ignore', value=ign)
        embed.add_field(name='anti-token・anti-raid', value=automod)

        ngembed = discord.Embed(
            title='NG Words', color=self.bot.Color,
            description="\n".join(
                nw for nw in self.settings[str(ctx.guild.id)]["ngword"]
            )
        )
        await ctx.send(embeds=[embed, ngembed])

    @automod.command()
    async def role(
        self, ctx: commands.Context, type_: Literal["admin", "mod"],
        mode: Literal["add", "remove"], role: TryConverter[discord.Role, discord.Object]
    ):
        await self.check_permissions("admin", ctx)
        assert ctx.guild

        if str(role.id) in self.settings[str(ctx.guild.id)][f'{type_}role']:
            if mode == "add":
                await ctx.send('このロールはすでに追加されています。')
            else:
                self.settings[str(ctx.guild.id)][f'{type_}role'].remove(
                    str(role.id))
                await self.save(ctx.guild.id)
                await ctx.send('削除完了しました。')
        else:
            if mode == "remove":
                await ctx.send('このロールは存在しません。')
            else:
                self.settings[str(ctx.guild.id)][f'{type_}role'].append(
                    str(role.id))
                await self.save(ctx.guild.id)
                await ctx.send('追加完了しました。')

    async def save(self, guild_id):
        self.data_check(guild_id)

        se = self.settings[str(guild_id)]
        await self.bot.execute_sql(
            """INSERT INTO AutoModSetting (
                GuildId, AdminRole, ModRole, MuteRole, AntiRaid,
                RaidAction, RaidActionTime, IgnoreChannel,
                IgnoreRole, NGWord, Duplct, Action, Tokens
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                AdminRole = VALUES(AdminRole), ModRole = VALUES(ModRole),
                MuteRole = VALUES(MuteRole), AntiRaid = VALUES(AntiRaid),
                RaidAction = VALUES(RaidAction),
                RaidActionTime = VALUES(RaidActionTime),
                IgnoreChannel = VALUES(IgnoreChannel),
                IgnoreRole = VALUES(IgnoreRole), NGWord = VALUES(NGWord),
                Duplct = VALUES(Duplct), Action = VALUES(Action),
                Tokens = VALUES(Tokens)
            ;""", (
                guild_id, dumps(se["adminrole"]), dumps(se["modrole"]),
                se["muterole"], se["antiraid"], se["raidaction"],
                se["raidactiontime"], dumps(se["ignore_channel"]),
                dumps(se["ignore_role"]), dumps(se["ngword"]),
                dumps(se["duplct"]), dumps(se["action"]), se["tokens"]
            )
        )

        async def sqler(cursor):
            await cursor.executemany(
                """INSERT INTO AutoModPunishments VALUES (
                    %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    GuildId = VALUES(GuildId), MemberId = VALUES(MemberID),
                    Strike = VALUES(Strike)
                ;""", ((guild_id, x1, x2) for x1, x2 in self.punishments[str(guild_id)].items())
            )
        await self.bot.execute_sql(sqler)


async def setup(bot: Bot):
    await bot.add_cog(AutoMod(bot))
