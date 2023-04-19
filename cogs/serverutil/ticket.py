import discord
from discord.ext import commands


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot, self.before = bot, ""

    @commands.group()
    async def ticket(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply("使用方法が違います")

    @ticket.command()
    async def panel(self, ctx, title, bttext, *, description):
        """
        NLang ja チケット作成用パネルコマンドです
        チケットを作成するためのパネルを送信します
        **使いかた：**
        EVAL self.bot.command_prefix+'ticket panel チケット名 ボタンの内容 embedの説明'
        ELang ja
        NLang default Panel command for creating tickets
        Submit a panel to create a ticket
        **How to use:**
        EVAL self.bot.command_prefix+'ticket panel ticket_name button_contents embed_description'
        ELang default
        """
        embed = discord.Embed(
            title=title, color=self.bot.Color, description=description)
        bts = list()
        button = discord.ui.Button(
            label=bttext, custom_id="sakuraticket", style=discord.ButtonStyle.green)
        bts.append(button)
        views = MainView(bts)
        await ctx.send(embeds=[embed], view=views)

    @ticket.command()
    async def close(self, ctx):
        """
        NLang ja チケットを閉じるコマンドです
        チケットを閉じるコマンドです。チケット作成者が実行できます。サーバーの管理者が削除したい場合はチャンネルをそのまま削除してください
        **使いかた：**
        EVAL self.bot.command_prefix+'ticket close'
        ELang ja
        NLang default Panel command for close tickets
        The command to close the ticket. Can be run by the ticket creator. if the server administrator wants to delete the channel simply
        **How to use:**
        EVAL self.bot.command_prefix+'ticket close'
        ELang default
        """
        if ctx.channel.topic.find('（sakuraticket') != -1:
            id = int(ctx.channel.topic[ctx.channel.topic.rfind(
                "（") + 13:ctx.channel.topic.rfind('）')])
            if id == ctx.author.id:
                for obj in ctx.channel.overwrites.keys():
                    perms = ctx.channel.overwrites_for(obj)
                    perms.read_messages = False
                    await ctx.channel.set_permissions(obj, overwrite=perms)
            else:
                await ctx.send("あなたは実行できません")
        else:
            await ctx.send("このチャンネルはチケットではありません")

    @ticket.command()
    async def hide(self, ctx):
        """
        NLang ja 見れるユーザーを減らします
        チケットチャンネルを見れなくします
        **使いかた：**
        EVAL self.bot.command_prefix+'ticket hide ユーザーメンション（複数可)'
        ELang ja
        NLang default reduces the number of users who can see
        Prevents you from seeing the ticket channel
        **How to use:**
        EVAL self.bot.command_prefix+'ticket hide users_mention'
        ELang default
        """
        str(ctx.message.content)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data or not interaction.guild or not interaction.message:
            return
        assert isinstance(interaction.user, discord.Member)

        if interaction.data.get("custom_id", "") == "sakuraticket":
            chan = interaction.channel
            cat = getattr(chan, "category", None)
            permission = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True)
            }
            ch = await interaction.guild.create_text_channel(name=f"{interaction.user.name}-{interaction.message.embeds[0].title}", overwrites=permission, category=cat, topic='（sakuraticket' + str(interaction.user.id) + '）')
            await interaction.response.send_message(content="作成しました", ephemeral=True)
            await ch.send(interaction.user.mention + "チャンネルを作成しました。閉じる場合は" + self.bot.command_prefix + "ticket closeと発言してください。ユーザをメンションすることで他のユーザーを参加させることも出来ます")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if not isinstance(msg.channel, discord.TextChannel):
            return
        if msg.channel.topic is None:
            return
        if msg.channel.topic.find('（sakuraticket') != -1:
            id = int(msg.channel.topic[msg.channel.topic.rfind(
                '（') + 13:msg.channel.topic.rfind('）')])
            if id == msg.author.id:
                if len(msg.mentions) != 0:
                    if msg.content.find(
                            self.bot.command_prefix + 'hide ') == 0:
                        for m in msg.mentions:
                            perms = msg.channel.overwrites_for(m)
                            perms.read_messages = False
                            await msg.channel.set_permissions(m, overwrite=perms)
                    else:
                        for m in msg.mentions:
                            perms = msg.channel.overwrites_for(m)
                            perms.read_messages = True
                            await msg.channel.set_permissions(m, overwrite=perms)


class MainView(discord.ui.View):
    def __init__(self, args):
        super().__init__(timeout=None)

        for txt in args:
            self.add_item(txt)


async def setup(bot):
    await bot.add_cog(Ticket(bot))
