import discord
from discord.ext import commands
import asyncio
import random


class reversi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def reversi(self, ctx):
        b = board(self.bot)
        await b.start(ctx)


class board():
    def __init__(self, bot):
        self.bot = bot
        self.h = 8
        self.w = 8
        self.bvb = 0
        self.boards = dict()
        self.users = dict()
        self.upboard = dict()
        self.omc = 0
        self.turn = 1
        self.varr = [-self.w, -self.w + 1, 1, self.w +
                     1, self.w, self.w - 1, -1, -self.w - 1]
        self.ck3 = 0
        self.ck3b = 1
        self.btu = 5

    def botf(self, xy, ub):
        tc = 0
        min = self.w * self.h
        max = 0
        mxd = 0
        mid = 0
        tmpc = 0
        try:
            if self.upboard[0] == 3:
                xy["x"] = 1
                xy["y"] = 1
                raise SyntaxError()
            if self.upboard[self.w - 1] == 3:
                xy["x"] = self.w
                xy["y"] = 1
                raise SyntaxError()
            if self.upboard[(self.h - 1) * self.w] == 3:
                xy["x"] = 1
                xy["y"] = self.h
                raise SyntaxError()
            if self.upboard[self.w * self.h - 1] == 3:
                xy["x"] = self.w
                xy["y"] = self.h
                raise SyntaxError()
            for lop in range(self.w * self.h):
                if self.upboard[lop] == 3:
                    tmpc = 0
                    tk = 0
                    if self.turn == 1:
                        tk = 2
                    elif self.turn == 2:
                        tk = 1
                    for bvi in range(8):
                        if ub[lop + (self.varr[bvi])] == tk:
                            ccc = lop + (self.varr[bvi])
                            while ub[ccc] == tk:
                                ccc = ccc + (self.varr[bvi])
                            if ub[ccc] == self.turn:
                                ccco = lop + (self.varr[bvi])
                                while ub[ccco] == tk:
                                    tmpc = tmpc + 1
                                    ccco = ccco + (self.varr[bvi])
                    if max == tmpc:
                        if random.randint(1, 2) == 1:
                            mxd = lop
                    if mid == tmpc:
                        if random.randint(1, 2) == 1:
                            mid = lop
                    if tmpc < min:
                        min = tmpc
                        mid = lop
                    if tmpc > max:
                        max = tmpc
                        mxd = lop
            if self.omc > self.w * self.h / 2:
                xy["x"] = mxd % self.w + 1
                xy["y"] = mxd / self.w + 1
            else:
                xy["x"] = mid % self.w + 1
                xy["y"] = mid / self.w + 1
        except SyntaxError:
            str("break")
        if (xy["y"] - 1) * self.w + (xy["x"] -
                                     1) > 63 or (xy["y"] - 1) * self.w + (xy["x"] - 1) < 0:
            for berr in range(self.h * self.w):
                if self.upboard[berr] == 3:
                    xy["x"] = berr % self.w + 1
                    xy["y"] = berr / self.w + 1
        elif self.upboard[(xy["y"] - 1) * self.w + (xy["x"] - 1)] != 3:
            for berr in range(self.h * self.w):
                if self.upboard[berr] == 3:
                    xy["x"] = berr % self.w + 1
                    xy["y"] = berr / self.w + 1

    def border(self, val):
        val = val + "◆"
        for c in range(self.w):
            val = val + \
                str(c + 1).translate(str.maketrans(
                    {chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)}))
        val = val + "◆\n"
        return val

    def pb(self, b):
        val = self.border("")
        for c in range(self.h):
            val = val + \
                str(c + 1).translate(str.maketrans(
                    {chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)}))
            for j in range(self.w):
                biwj = b[c * self.w + j]
                if biwj == 0:
                    val = val + "　"
                elif biwj == 1:
                    val = val + "〇"
                elif biwj == 2:
                    val = val + "●"
                elif biwj == 3:
                    val = val + "・"
            val = val + str(c + 1).translate(str.maketrans(
                {chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})) + "\n"
        val = self.border(val)
        return val

    def oend(self):
        bkc = 0
        wkc = 0
        for ecc in range(self.w * self.h):
            if self.boards[ecc] == 1:
                bkc = bkc + 1
            elif self.boards[ecc] == 2:
                wkc = wkc + 1
        if bkc < wkc:
            return self.users[1] + "の勝ち"
        if bkc > wkc:
            return self.users[0] + "の勝ち"
        if bkc == wkc:
            return "引き分け"

    async def o(self, board, msg, ctx):
        val = ""
        resend = False
        start = ((self.h - 2) / 2) * self.w + ((self.w - 2) / 2)
        board[start] = 2
        board[start + 1] = 1
        board[start + self.w + 1] = 2
        board[start + self.w] = 1
        for bvcfr in range(self.w * self.h):
            self.boards[bvcfr] = board[bvcfr]
        ebd = msg.embeds[0]
        while True:
            if self.omc == self.w * self.h:
                ebd.description = self.oend()
                await msg.edit(embeds=[ebd])
                return
            if self.turn == 1:
                val = "◎" + self.users[0] + "|　" + self.users[1] + "\n"
            else:
                val = "　" + self.users[0] + "|◎" + self.users[1] + "\n"
            val = val + self.upb(self.boards)
            if resend:
                await msg.delete()
                ebd = discord.Embed(
                    title="オセロ", description=val, color=self.bot.Color)
                msg = await ctx.send(embeds=[ebd])
                resend = False
            else:
                ebd.description = val
                await msg.edit(embeds=[ebd])
            x = 0
            y = 0
            if self.ck3 == 0:
                if self.ck3b == 0:
                    ebd.description = "どちらも置ける場所がない為終了します。\n" + \
                        (self.oend() or "")
                    await msg.edit(embeds=[ebd])
                    return
                val = "置ける場所がない為スキップされました。"
                ebd.description = val
                await msg.edit(embeds=[ebd])
                self.ck3b = self.ck3
                for i in range(self.w * self.h):
                    self.upboard[i] = 0
                if self.turn == 1:
                    self.turn = 2
                else:
                    self.turn = 1
                self.ck3 = 0
                continue
            if self.btu == self.turn:
                xy = dict()
                self.botf(xy, self.boards)
                x = int(xy["x"])
                y = int(xy["y"])
            else:
                if self.bvb:
                    xy = dict()
                    self.botf(xy, self.boards)
                    x = int(xy["x"])
                    y = int(xy["y"])
                else:
                    tmp = (await self.input(ctx, "置く位置を指定してください(横,縦)　例: 3,2")).content
                    xy = tmp.split(",")
                    x = int(xy[0])
                    y = int(xy[1])
                    resend = True
            if self.upboard[(y - 1) * self.w + (x - 1)] == 3:
                self.boards[(y - 1) * self.w + (x - 1)] = self.turn
                self.om((y - 1) * self.w + (x - 1), self.boards)
                self.ck3b = self.ck3
                for i in range(self.w * self.h):
                    self.upboard[i] = 0
                if self.turn == 1:
                    self.turn = 2
                else:
                    self.turn = 1
                self.ck3 = 0

    def om(self, xy, ub):
        self.omc = self.omc + 1
        tk = 0
        if self.turn == 1:
            tk = 2
        else:
            tk = 1
        sty = ""
        for bvi in range(8):
            if ub[xy + (self.varr[bvi])] == tk:
                ccc = xy + (self.varr[bvi])
                while ub[ccc] == tk:
                    ccc = ccc + (self.varr[bvi])
                if ub[ccc] == self.turn:
                    ccco = xy + (self.varr[bvi])
                    while ub[ccco] == tk:
                        self.boards[ccco] = self.turn
                        ccco = ccco + (self.varr[bvi])

    def upb(self, ub):
        for ppp in range(self.w * self.h):
            if ub[ppp] == 3:
                ub[ppp] = 0
        tk = 0
        if self.turn == 1:
            tk = 2
        else:
            tk = 1
        for bi in range(self.w * self.h):
            if ub[bi] == self.turn:
                for bvi in range(8):
                    try:
                        if ub[bi + (self.varr[bvi])] == tk:
                            if not ub[bi + (self.varr[bvi])] == 0:
                                ccc = bi + (self.varr[bvi])
                                while ub[ccc] == tk:
                                    if bvi < 4:
                                        if (ccc + (self.varr[bvi])
                                                ) % 8 == self.w + 1:
                                            raise SyntaxError("break")
                                    else:
                                        if (ccc + (self.varr[bvi])
                                                ) % 8 == self.w - 1:
                                            raise SyntaxError("break")
                                    ccc = ccc + (self.varr[bvi])
                                if ub[ccc] == 0:
                                    ub[ccc] = 3
                                    self.upboard[ccc] = 3
                                    self.ck3 = self.ck3 + 1
                    except SyntaxError:
                        str("break")
        return self.pb(ub)

    async def start(self, ctx):
        self.users[0] = "黒"
        self.users[1] = "白"
        math = dict()
        for i in range(self.w * self.h):
            math[i] = 0
        for i in range(self.w * self.h):
            self.upboard[i] = 0
        val = "ゲームモード選択\n1 . pvp\n2 . pve\n"
        ebd = discord.Embed(title="オセロ", description=val, color=self.bot.Color)
        msg = await ctx.send(embeds=[ebd])
        imu = int((await self.input1(ctx, "ゲームモードを選んで数字を送信してください")).content)
        if imu == 1:
            self.uid = dict()
            self.uid[1] = ctx.author.id
            self.uid[2] = int((await self.input1(ctx, "対戦相手のuseridを入力してください")).content)
        if imu == 2:
            self.uid = dict()
            self.uid[1] = ctx.author.id
            self.btu = 2
        elif imu == 3:
            self.btu = 1
            self.bvb = 1
        self.pb(math)
        await self.o(math, msg, ctx)

    async def input1(self, ctx, q):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout=180.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break

    async def input(self, ctx, q):
        def check(m):
            return m.author.id == self.uid[self.turn] and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=180.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await self.bot.wait_for('message', timeout=180.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break


async def setup(bot):
    await bot.add_cog(reversi(bot))
