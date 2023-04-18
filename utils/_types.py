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
    Purge: purge.Purge
    BotAbout: about.BotAbout
    ErrorQuery: errors.ErrorQuery
    Help: help.Help
    Prefix: prefix.Prefix
    SpeedTest: speedtest.SpeedTest
    Websocket: websocket.Websocket
    GameSearch: gamesearch.GameSearch
    Music: music.Music
    MyNews: mynews.MyNews
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
    Bump: bump.Bump
    Captcha: captcha.Captcha
    FreeThread: freethread.FreeThread
    Gban: gban.Gban
    Giveaway: giveaway.Giveaway
    GlobalChat: globalchat.GlobalChat
    KasoNotice: kaso_notice.KasoNotice
    Rocations: rocations.Rocations
    RoleLinker: role_linker.RoleLinker
    Ticket: ticket.Ticket
    TTS: tts.TTS

class GuildContext(commands.Context):
    "commands.guild_onlyをデコレータとしてつけた場合にctxに型付けできるクラス。"
    author: discord.Member
    guild: discord.Guild
