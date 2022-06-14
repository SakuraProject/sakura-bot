import stripe
from discord.ext import commands
import urllib
import discord
import asyncio
import os
from ujson import loads,dumps
secretkey=os.environ["YMARTKEY"]
class shopping(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    @commands.group(
        aliases=["買い物"]
    )
    async def shopping(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います。")
    @shopping.command()
    async def cart(self,ctx):
        async with self.bot.session.get("https://ystore.jp/api/cart.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(ctx.author.id)+"&distag="+urllib.parse.quote_plus(ctx.author.name+'#'+ctx.author.discriminator)) as resp:
            rpt = await resp.text()
            if rpt=="[]":
                await ctx.reply("カートに商品がありません")
            else:
                dcr=""
                price=0
                gj = loads(rpt)
                for itm in gj:
                    row=itm["row"]
                    v=itm["v"]
                    images=itm["images"]
                    if int(row["lotof"])>=int(v["lotof"]):
                        price= price + int(v["price"])*int(v["lotof"])
                        dcr = dcr + v["itemname"] + "×"+ v["lotof"] + "→" + str(int(v["price"])*int(v["lotof"])) + "円\n"
                    else:
                        dcr = dcr + v["itemname"] + "(現在在庫不足[要求:"+ v["lotof"] + "、在庫:" + row["lotof"] + ")→0円\n"
                dcr = dcr + "計" + str(price) + "円"
                ebd = discord.Embed(title="カート",description=dcr,color=self.bot.Color)
                await ctx.send(embeds=[ebd])
    @shopping.command()
    async def search(self,ctx,word):
        async with self.bot.session.get("https://ystore.jp/api/search.php?q="+urllib.parse.quote_plus(word, encoding='utf-8')) as resp:
            rpt = await resp.text()
            if rpt=="[]":
                await ctx.reply("すみません。何も見つかりませんでした")
            else:
                gj = loads(rpt)
                vie = discord.ui.View()
                vie.add_item(SearchList(gj))
                await ctx.send("見たい商品を選択してください",view=vie)
    @shopping.command()
    async def address(self,ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        reqdata = dict()
        reqdata["secret"] = secretkey
        reqdata["disid"] = str(ctx.author.id)
        reqdata["distag"] = ctx.author.name+'#'+ctx.author.discriminator
        await ctx.author.send("配送先住所設定を開始します")
        await ctx.send("DMを確認してください")
        await ctx.author.send("郵便番号を入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            reqdata["pcode"] = message.content
        await ctx.author.send("住所を入力してください")
        try:
            message = await client.wait_for('message', timeout= 180.0, check= check)
        except asyncio.TimeoutError:
            await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            reqdata["postal"] = message.content
        await ctx.author.send("受取人名を入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.author.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            reqdata["name"] = message.content
        await ctx.author.send("電話番号を入力してください")
        try:
            message = await client.wait_for('message', timeout= 180.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            reqdata["tel"] = message.content
        async with self.bot.session.post("http://ystore.jp/api/postset.php",data=reqdata) as resp:
            rpt = await resp.text()

    async def input(self,ctx,q):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send(q)
        while True:
            try:
                message = await client.wait_for('message', timeout= 180.0, check= check)
            except asyncio.TimeoutError:
                await ctx.channel.send('入力を待機中です。キャンセルする場合は「キャンセルする」と送ってください')
            else:
                if message.content == "キャンセルする":
                    raise SyntaxError()
                await ctx.channel.send("入力を受け付けました。確定する場合は「ok」と送って下さい。やり直す場合は「修正」と送ってください")
                while True:
                    try:
                        message1 = await client.wait_for('message', timeout= 180.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.channel.send('タイムアウトしました。入力をやりなおしてください')
                        break
                    else:
                        if message1.content == "ok":
                            return message
                        elif message1.content == "修正":
                            break
    @shopping.command()
    async def ticket(self,ctx):
        if ctx.guild!=None:
            await ctx.send("このコマンドはDM専用です")
            return
        async with self.bot.session.get("https://ystore.jp/api/cart.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(ctx.author.id)+"&distag="+urllib.parse.quote_plus(ctx.author.name+'#'+ctx.author.discriminator)) as resp:
            rpt = await resp.text()
            if rpt=="[]":
                await ctx.reply("まだ注文はありません")
            else:
                gi = loads(rpt)
                eb = discord.Embed(title="注文一覧",color=self.bot.Color)
                for t in gi:
                    eb.add_field(name=t["v"]["itemname"],value="個数:"+t["v"]["lotof"]+"\n決済金額:"+t["v"]["prices"]+"配送先住所:"+t["v"]["postal"]+"\n"+t["v"]["name"]+"\n電話番号："+t["v"]["tel"]+"\n購入者の連絡先\n"+t["name"]+"\n"+t["tel"])
                await ctx.author.send(embeds=[eb])

    @shopping.command()
    async def sell(self,ctx):
        await ctx.send("出品を開始します")
        req = dict()
        req["secret"] = secretkey
        req["disid"] = str(ctx.author.id)
        req["distag"] = ctx.author.name+'#'+ctx.author.discriminator
        try:
            req["tit"] = (await self.input(ctx,"商品名を入力してください")).content
            req["vl"] = (await self.input(ctx,"商品説明を入力してください")).content
            imgm = await self.input(ctx,"商品画像を送信してください")
            imgj = list()
            for fis in imgm.attachments:
                req1 = dict()
                req1["url"] = fis.url
                req1["fname"] = fis.filename
                req1["secret"] = secretkey
                req1["disid"] = str(ctx.author.id)
                req1["distag"] = ctx.author.name+'#'+ctx.author.discriminator
                async with self.bot.session.post("http://ystore.jp/api/copyimg.php",data=req1) as resp1:
                    rpt = await resp1.text()
                    imgj.append(rpt)
            req["imgs"] = dumps(imgj)
            req["price"] = (await self.input(ctx,"金額を数字で入力してください")).content
            req["lotof"] = (await self.input(ctx,"在庫を数字で入力してください")).content
            async with self.bot.session.get("https://ystore.jp/api/cats.php") as resp:
                rpt = await resp.text()
            catarr = loads(rpt)
            ctls = ""
            i = 1
            for cat in catarr:
                ctls = ctls + "No." + str(i) + cat["name"] + "\n"
                i = i + 1
            evd = discord.Embed(title="カテゴリ一覧",description=ctls,color=self.bot.Color)
            await ctx.send(embeds=[evd])
            cno = int((await self.input(ctx,"カテゴリを選んでカテゴリーナンバーを数値で送信してください")).content)
            req["category"] = catarr[cno-1]
            async with self.bot.session.post("http://ystore.jp/api/add.php",data=req) as resp:
                rpt = await resp.text()
                await ctx.send(rpt)
        except SyntaxError:
            await ctx.send("キャンセルしました")

    @shopping.command()
    async def edit(self,ctx):
        req = dict()
        async with self.bot.session.get("https://ystore.jp/api/items.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(ctx.author.id)+"&distag="+urllib.parse.quote_plus(ctx.author.name+'#'+ctx.author.discriminator)) as resp:
            rpt = await resp.text()
            if rpt=="[]" or rpt=="null":
                await ctx.reply("出品した商品がありません")
                return
            gj = loads(rpt)
            ctls = ""
            i = 1
            for cat in gj:
                ctls = ctls + "No." + str(i) + cat["v"]["itemname"] + "\n"
                i = i + 1
            evd = discord.Embed(title="出品一覧",description=ctls,color=self.bot.Color)
            await ctx.send(embeds=[evd])
            cno = int((await self.input(ctx,"編集する商品を選んで商品ナンバーを数値で送信してください")).content)
            req["i"] = gj[cno-1]["v"]["itemid"]
        await ctx.send("編集を開始します")
        req["secret"] = secretkey
        req["disid"] = str(ctx.author.id)
        req["distag"] = ctx.author.name+'#'+ctx.author.discriminator
        try:
            req["tit"] = (await self.input(ctx,"商品名を入力してください")).content
            req["vl"] = (await self.input(ctx,"商品説明を入力してください")).content
            imgm = await self.input(ctx,"商品画像を送信してください")
            imgj = list()
            for fis in imgm.attachments:
                req1 = dict()
                req1["url"] = fis.url
                req1["fname"] = fis.filename
                req1["secret"] = secretkey
                req1["disid"] = str(ctx.author.id)
                req1["distag"] = ctx.author.name+'#'+ctx.author.discriminator
                async with self.bot.session.post("http://ystore.jp/api/copyimg.php",data=req1) as resp1:
                    rpt = await resp1.text()
                    imgj.append(rpt)
            req["imgs"] = dumps(imgj)
            req["price"] = (await self.input(ctx,"金額を数字で入力してください")).content
            req["lotof"] = (await self.input(ctx,"在庫を数字で入力してください")).content
            async with self.bot.session.get("https://ystore.jp/api/cats.php") as resp:
                rpt = await resp.text()
            catarr = loads(rpt)
            ctls = ""
            i = 1
            for cat in catarr:
                ctls = ctls + "No." + str(i) + cat["name"] + "\n"
                i = i + 1
            evd = discord.Embed(title="カテゴリ一覧",description=ctls,color=self.bot.Color)
            await ctx.send(embeds=[evd])
            cno = int((await self.input(ctx,"カテゴリを選んでカテゴリーナンバーを数値で送信してください")).content)
            req["category"] = catarr[cno-1]
            async with self.bot.session.post("http://ystore.jp/api/edit.php",data=req) as resp:
                rpt = await resp.text()
                await ctx.send(rpt)
        except SyntaxError:
            await ctx.send("キャンセルしました")

    @shopping.command()
    async def bank(self,ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        await ctx.author.send("売上金振込口座の設定を開始します")
        req = dict()
        req["secret"] = secretkey
        req["disid"] = str(ctx.author.id)
        req["distag"] = ctx.author.name+'#'+ctx.author.discriminator
        await ctx.send("DMを確認してください")
        await ctx.author.send("銀行名を入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            req["ginko"]=message.content
        await ctx.author.send("支店名を入力してください")
        try:
            message = await client.wait_for('message', timeout= 120.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            req["siten"]=message.content
        await ctx.author.send("口座番号を入力してください")
        try:
            message = await client.wait_for('message', timeout= 180.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            req["code"]=message.content
        await ctx.author.send("口座名義を入力してください")
        try:
            message = await client.wait_for('message', timeout= 90.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            req["name"]=message.content
        async with self.bot.session.post("http://ystore.jp/api/ginko.php",data=req) as resp:
            rpt = await resp.text()
            await ctx.send(rpt)

    @shopping.command()
    async def pay(self,ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        cnum=""
        year=""
        mon=""
        cvc=""
        await ctx.author.send("決済を開始します")
        await ctx.send("DMを確認してください")
        await ctx.author.send("クレジットカード番号を入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            cnum=message.content.replace(" ","").replace("-","")
        await ctx.author.send("カードの有効期限を入力してください(例:yyyy/mm")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            spl=message.content.split("/")
            year=spl[0]
            mon=spl[1]
        await ctx.author.send("cvc(セキュリティコード)を入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await ctx.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            cvc=message.content
        async with self.bot.session.get("http://ystore.jp/api/getpayd.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(ctx.author.id)+"&distag="+urllib.parse.quote_plus(ctx.author.name+'#'+ctx.author.discriminator)) as resp:
            rpt = await resp.text()
        stripe.api_key = os.environ["STRIPEKEY"]
        try:
            pm=stripe.PaymentMethod.create(type="card",card={"number": cnum,"exp_month": int(mon),"exp_year": int(year),"cvc": cvc,})
            payment_intent = stripe.PaymentIntent.create(
                amount=rpt,# 支払金額
                currency='jpy',# 利用通貨
                customer=None,# CustomerオブジェクトID
                payment_method=pm["id"],# 支払いに使用するクレジットカード
                off_session=True,# 支払いの実行時に顧客が決済フローに存在しないことを示す
                confirm=True,# PaymentIntentの作成と確認を同時に行う
                )
            async with self.bot.session.get("https://ystore.jp/api/payd.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(ctx.author.id)+"&distag="+urllib.parse.quote_plus(ctx.author.name+'#'+ctx.author.discriminator)) as resp:
                await ctx.author.send("決済成功しました")
        except Exception as e:
            await ctx.author.send("このカードは使用出来ませんでした")

class SearchList(discord.ui.Select):
    def __init__(self,args):
        self.its=args
        options=[]
        for item in args:
            options.append(discord.SelectOption(label=item["itemname"], description=''))
    
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for item in self.its:
            if item["itemname"] == self.values[0]:
                ebd = discord.Embed(title=item["itemname"],description=item["vl"],color=self.bot.Color)
                img = "https://ystore.jp/itemimg/"+loads(item["image"])[0]
                ebd.set_image(url=img)
                ebd.add_field(name="価格",value=item["price"])
                vie = discord.ui.View()
                vie.add_item(ImgList(item,loads(item["image"])))
                vie.add_item(CartButton(item))
                await interaction.response.edit_message(embeds=[ebd],view=vie)

class CatList(discord.ui.Select):
    def __init__(self,req,args):
        self.req=req
        options=[]
        for item in args:
            options.append(discord.SelectOption(label=item["name"], description=''))
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        req["category"] = self.values[0]
        
class ImgList(discord.ui.Select):
    def __init__(self,ite,args):
        self.its=args
        self.it=ite
        options=[]
        i=1
        for item in args:
            options.append(discord.SelectOption(label=str(i)+"枚目の画像を表示", description=''))
            i = i + 1
        super().__init__(placeholder='', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        ebd = discord.Embed(title=self.it["itemname"],description=self.it["vl"],color=self.bot.Color)
        inb = int(self.values[0].replace("枚目の画像を表示",""))
        img = "https://ystore.jp/itemimg/"+self.its[inb]
        ebd.set_image(url=img)
        ebd.add_field(name="価格",value=self.it["price"])
        vie = discord.ui.View()
        vie.add_item(ImgList(self.it,self.its))
        vie.add_item(CartButton(self.it))
        await interaction.response.edit_message(embed=ebd,view=vie)
class CartButton(discord.ui.Button):
    def __init__(self,it):
        self.it = it
        super().__init__(label="カートに追加",style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        await interaction.response.send_message("いくつ追加しますか。数字で入力してください")
        try:
            message = await client.wait_for('message', timeout= 60.0, check= check)
        except asyncio.TimeoutError:
            await interaction.channel.send('タイムアウトしました.  再度操作をやり直してね')
            return
        else:
            async with client.session.get("https://ystore.jp/api/addcart.php?secret="+urllib.parse.quote_plus(secretkey, encoding='utf-8')+"&disid="+str(interaction.user.id)+"&distag="+urllib.parse.quote_plus(interaction.user.name+'#'+interaction.user.discriminator)+"&lof="+message.content+"&i="+self.it["itemid"]) as resp:
                rpt = await resp.text()
                await interaction.channel.send(rpt)
async def setup(bot):
    global client
    client = bot
    await bot.add_cog(shopping(bot))
