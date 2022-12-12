# Sakura Utils - Types

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from cogs.automod import automod, mod, purge
    from cogs.bot import about, errors, help, prefix, speedtest, websocket
    from cogs.entertainment import gamesearch, music, mynews, qr, reversi
    from cogs.individual import (
        afk, individual, mail, obj_info, onlinenotice, sakurapoint, schedule,
        shopping, tweet
    )
    from cogs.sakurabrand import ad, plugin
    from cogs.serverutil import (
        bump, captcha, freethread, gban, giveaway, globalchat, kaso_notice,
        rocations, role_linker, ticket, tts
    )

class Cogs(TypedDict):
    AutoMod: automod.AutoMod
    Mod: mod.Moderation
    purge: purge.Purge
    BotAbout: about.BotAbout
    ErrorQuery: errors.ErrorQuery
    Help: help.Help
    Prefix: prefix.Prefix
    speedtest: speedtest.speedtest
    Websocket: websocket.Websocket
    GameSearch: gamesearch.GameSearch
    music: music.music
    mynews: mynews.mynews
    qr: qr.qr
    reversi: reversi.reversi
    Afk: afk.Afk
    Individual: individual.Individual
    Mail: mail.Mail
    ObjectInfo: obj_info.ObjectInfo
    OnlineNotice: onlinenotice.OnlineNotice
    SakuraPoint: sakurapoint.SakuraPoint
    schedule: schedule.schedule
    shopping: shopping.shopping
    Tweet: tweet.Tweet
    SakuraAd: ad.SakuraAd
    Plugin: plugin.Plugin
    bump: bump.bump
    Captcha: captcha.Captcha
    FreeThread: freethread.FreeThread
    Gban: gban.Gban
    giveaway: giveaway.giveaway
    GlobalChat: globalchat.GlobalChat
    KasoNotice: kaso_notice.KasoNotice
    rocations: rocations.rocations
    RoleLinker: role_linker.RoleLinker
    ticket: ticket.ticket
    tts: tts.tts

class GuildContext(commands.Context):
    "commands.guild_onlyをデコレータとしてつけた場合にctxに型付けできるクラス。"
    author: discord.Member
    guild: discord.Guild
