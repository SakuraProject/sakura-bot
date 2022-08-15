from discord.utils import get
import discord
from discord.ext import commands
import os
from ujson import loads, dumps
from os import listdir
import subprocess
import asyncio
import aiofiles
if not os.path.exists("VITS"):
    cmd = "git clone https://github.com/zassou65535/VITS.git"
    subprocess.call(cmd.split())
    cmd = "python setup.py build_ext --inplace"
    subprocess.call(cmd.split(),cwd="./VITS/module/model_component/monotonic_align/")
from VITS.module.vits_generator import VitsGenerator
import torch
import random
import pyopenjtalk
import torchaudio

class tts(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.pl = [' ', 'I', 'N', 'U', 'a', 'b', 'by', 'ch', 'cl', 'd', 'dy', 'e', 'f', 'g', 'gy', 'h', 'hy', 'i', 'j', 'k', 'ky', 'm', 'my', 'n', 'ny', 'o', 'p', 'py', 'r', 'ry', 's', 'sh', 't', 'ts', 'ty', 'u', 'v', 'w', 'y', 'z']
        self.pi = {p : i for i, p in enumerate(self.pl, 0)}
        se = 999
        random.seed(se)
        torch.manual_seed(se)
        self.dt = ("cuda:0" if torch.cuda.is_available() else "cpu")
        self.device = torch.device(self.dt)
        self.gen = VitsGenerator(n_phoneme=len(self.pl), n_speakers=100)
        self.rch = list()
        self.voice = dict()
        self.dic = dict()
        self.odic = "data/tts/OpenJTalk/dic"
        #additional tts settings
        self.ttsserverurl = "" # server url on assistant seika
        self.basicuser = "" #username
        self.basicpass = "" #password

    async def cog_load(self):
        ctsql = "CREATE TABLE if not exists `tts` (`gid` BIGINT NOT NULL,`voice` VARCHAR(100) NOT NULL,`dic` JSON NULL) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;"
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(ctsql)
                await cur.execute("SELECT * FROM `tts`")
                res = await cur.fetchall()
                for r in res:
                    self.voice[str(r[0])] = r[1]
                    if r[2] != None:
                        self.dic[str(r[0])] = loads(r[2])

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.channel.id in self.rch:
            voice = get(self.bot.voice_clients, guild=message.guild)
            if not voice == None:
                sc = message.content
                embeds = message.embeds
                if embeds is not None:
                    for e in embeds:
                        if isinstance(e.description, str):
                            sc = sc + embed.description
                        if e.fields is not None:
                            for fi in e.fields:
                                sc = sc + fi.name + fi.value
                sc = sc.strip()
                swav = str(message.id) + ".wav"
                self.dic.setdefault(str(message.guild.id), dict())
                for dt in self.dic[str(message.guild.id)].keys():
                     sc = sc.replace(dt,self.dic[str(message.guild.id)][dt])
                self.voice.setdefault(str(message.guild.id), "mei.htsvoice")
                if self.voice[str(message.guild.id)].endswith(".htsvoice"):
                    args = ["open_jtalk", "-x", self.odic, "-m", "data/tts/voices/" + self.voice[str(message.guild.id)] + "/" + self.voice[str(message.guild.id)], '-r', '1.0', '-ow', swav]
                    subprocess.run(args, input=sc.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif self.voice[str(message.guild.id)].endswith(".pth"):
                    self.gen.load_state_dict(torch.load("data/tts/voices/" + self.voice[str(message.guild.id)] + "/" + self.voice[str(message.guild.id)]))
                    g = self.gen.to(self.device)
                    g.eval()
                    p = [pyopenjtalk.g2p(element) for element in sc if(not element=="")]
                    p = [element.replace(" ",",") for element in p]
                    p = ', ,'.join(p).replace("\n", "").split(",")
                    conv = [self.pi[t] for t in p]
                    foo = [0] * (len(conv) * 2 + 1)
                    foo[1::2] = conv
                    p = torch.LongTensor(foo).to(self.device)
                    l = torch.tensor([p.size()[-1]], dtype=torch.long).to(self.device)
                    sl = torch.tensor([0], dtype=torch.long).to(self.device)
                    o = g.text_to_speech(text_padded=p.unsqueeze(0), text_lengths=l, speaker_id=sl)[0].data.cpu()
                    torchaudio.save(swav, o, sample_rate=22050)
                elif self.voice[str(message.guild.id)].endswith(".vvx"):
                    sid = self.voice[str(message.guild.id)].replace(".vvx","")
                    req = dict()
                    req["text"] = sc
                    req["speaker"] = sid
                    async with self.bot.session.post("https://localhost:50021/audio_query",data=req) as resp:
                        rpt = await resp.text()
                    async with self.bot.session.post("https://localhost:50021/synthesis",json=dumps(req.json())) as resp:
                        async with aiofiles.open(swav, "wb") as fp:
                            fp.write(await resp.read())
                elif self.voice[str(message.guild.id)].endswith(".tsv"):
                    sid = self.voice[str(message.guild.id)].replace(".tsv","")
                    req = dict()
                    req["talktext"] = sc
                    async with self.bot.session.post(f"http://{self.basicuser}:{self.basicpass}@{self.ttsserverurl}/SAVE2/{sid}",json=req) as resp:
                        async with aiofiles.open(swav, "wb") as fp:
                            fp.write(await resp.read())
                voice.play(discord.FFmpegPCMAudio(swav))
                while voice.is_playing():
                    await asyncio.sleep(1)
                os.remove(swav)
            else:
                self.rch.remove(message.channel.id)

    @commands.group()
    async def tts(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @tts.command()
    async def join(self,ctx,ch :discord.TextChannel=None):
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        if ch == None:
            ch = ctx.channel
        self.rch.append(ch.id)
        await ctx.send("読み上げを開始します")

    @tts.command()
    async def voice(self, ctx):
        lis = []
        option = []
        for name in listdir("data/tts/voices"):
            with open("data/tts/voices/" + name + "/name.txt") as f:
                vname = f.read()
            if len(option) == 20:
                lis.append(VoiceList(self.bot,self,option))
                option = []
            option.append(discord.SelectOption(label=vname,value=name))
        if self.ttsserverurl != "":
            async with self.bot.session.get(f"http://{self.basicuser}:{self.basicpass}@{self.ttsserverurl}/AVATOR2") as resp:
                j = await resp.json()
            for v in j:
                if len(option) == 20:
                    lis.append(VoiceList(self.bot,self,option))
                    option = []
                option.append(discord.SelectOption(label=v["name"],value=str(v["cid"])+".tsv"))
        lis.append(VoiceList(self.bot,self,option))
        await ctx.send("音声を選んでください",view=MainView(lis))

    @tts.command()
    async def disconnect(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        await voice.disconnect()

    @tts.command()
    async def dicadd(self,ctx,text,replased):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `tts` where `gid` = %s", ( interaction.guild.id,))
                res = await cur.fetchall()
                await conn.commit()
                self.dic.setdefault(str(ctx.guild.id), dict())
                self.dic[str(ctx.guild.id)][text] = replased
                if len(res) == 0:
                    await cur.execute("INSERT INTO `tts` (`gid`, `voice`, `dic`) VALUES (%s,%s,%s);", (interaction.guild.id,self.values[0],dumps(self.dic[str(ctx.guild.id)])))
                else:
                    await cur.execute("UPDATE `tts` SET `dic` = %s where `gid` = %s;", (dumps(self.dic[str(ctx.guild.id)]),interaction.guild.id))
                await ctx.send("登録しました")

    @tts.command()
    async def dicremove(self,ctx,text):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `tts` where `gid` = %s", ( interaction.guild.id,))
                res = await cur.fetchall()
                await conn.commit()
                self.dic.setdefault(str(ctx.guild.id), dict())
                self.dic[str(ctx.guild.id)].pop(text)
                if len(res) == 0:
                    await cur.execute("INSERT INTO `tts` (`gid`, `voice`, `dic`) VALUES (%s,%s,%s);", (interaction.guild.id,self.values[0],dumps(self.dic[str(ctx.guild.id)])))
                else:
                    await cur.execute("UPDATE `tts` SET `dic` = %s where `gid` = %s;", (dumps(self.dic[str(ctx.guild.id)]),interaction.guild.id))
                await ctx.send("削除しました")

class VoiceList(discord.ui.Select):
    def __init__(self, bot,cog,option):
        self.bot = bot
        self.cog = cog
        super().__init__(placeholder='', min_values=1, max_values=1, options=option)

    async def callback(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM `tts` where `gid` = %s", ( interaction.guild.id,))
                res = await cur.fetchall()
                await conn.commit()
                self.cog.voice[str(interaction.guild.id)] = self.values[0]
                if len(res) == 0:
                    await cur.execute("INSERT INTO `tts` (`gid`, `voice`, `dic`) VALUES (%s,%s,%s);", (interaction.guild.id,self.values[0],dumps(dict())))
                else:
                    await cur.execute("UPDATE `tts` SET `voice` = %s where `gid` = %s;", (self.values[0],interaction.guild.id))
                await interaction.response.send_message("音声を設定しました")
class MainView(discord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for txt in args:
            self.add_item(txt)
async def setup(bot):
    await bot.add_cog(tts(bot))
