import discord
from discord.ext import commands
class infomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_badge = {"UserFlags.verified_bot_developer","<:verified_bot_developer:991964080292233306>","UserFlags.early_supporter":"<:early_supporter:991963681502003230>","UserFlags.staff":"<:discord_staff:991963642729869372>","UserFlags.partner":"<:partnered_server_owner:991964149884137472>","UserFlags.hypesquad":"<:discord_HypeSquad_disc:991962182604566639>","UserFlags.bug_hunter":"<:bug_hunter:991963877770276944>","UserFlags.hypesquad_bravery":"<:discord_hypesquad_bravery_disc:991962211641741392>","UserFlags.hypesquad_brilliance":"<:discord_hypesquad_briliance_disc:991962274816331796>","UserFlags.hypesquad_balance":"<:discord_hypesquad_balance_disc:991962200879157288>"}
        self.bt = "<:discord_Bot_disc:991962236706885734>"
        self.vbt = "<:verified_bot:991963186234413139> <:system:991963778226847814>"
    @commands.command(
        aliases=["ui","���[�U�[���"]
    )
    async def userinfo(self, ctx: commands.Context,user:discord.User =None):
        """
        NLang ja ���[�U�[����\������R�}���h�ł�
        ���[�U�[����\������R�}���h�ł�
        **�g�������F**
        EVAL self.bot.command_prefix+'userinfo ���[�U�[id'
        EVAL self.bot.command_prefix+'userinfo'
        ELang ja
        NLang default Sorry, this command only supports Japanese.
        Sorry, this command only supports Japanese.
        ELang default
        """
        ebds = list()
        if user == None:
            user = ctx.author
        badge = ""
        for flg in user.public_flags.all():
             badge = self.user_badge.get(flg,"")
        name = user.name+'#'+user.discriminator
        if user.bot:
            if user.public_flags.verified_bot:
                name = name + self.vbt
            else:
                name = name + self.bt
        ebd = discord.Embed(title=user.name+'#'+user.discriminator+'�̏��',color=self.bot.Color)
        ebd.add_field(name="ID",value="```" + user.id + "```")
        ebd.add_field(name="�A�J�E���g�쐬��",value="<t:" + str(int(time.miktime(user.created_at.timetuple()))) + ":R>")
        ebd.add_field(name="�A�C�R��url",value=user.avatar.url)
        member = ctx.guild.get_user(user.id)
        if member != None:
            if meber.guild_avatar != None:
                ebd.add_field(name="���̃T�[�o�[�ł̃A�C�R��url",value=member.guild_avatar.url)
            ebd.add_field(name="�\����",value=user.member.display_name)
            ebd.add_field(name="�T�[�o�[�ւ̎Q����",value="<t:" + str(int(time.mktime(user.member.joined_at.timetuple()))) + ":R>")
        ebds.append(ebd)
        if member != None:
            user = member
            roles = ""
            for r in user.roles:
                roles = roles + " " + r.mention
            if member.guild_permissions.administrator:
                send=send+':o:�Ǘ���\n'
            else:
                send=send+':x:�Ǘ���\n'
            if user.guild_permissions.ban_members:
                send=send+':o:���[�U�[��ban\n'
            else:
                send=send+':x:���[�U�[��ban\n'
            if user.guild_permissions.kick_members:
                send=send+':o:���[�U�[��kick\n'
            else:
                send=send+':x:���[�U�[��kick\n'
            if user.guild_permissions.manage_channels:
                send=send+':o:�`�����l���̊Ǘ�\n'
            else:
                send=send+':x:�`�����l���̊Ǘ�\n'
            if user.guild_permissions.create_instant_invite:
                send=send+':o:���҃����N���쐬\n'
            else:
                send=send+':x:���҃����N���쐬\n'
            if user.guild_permissions.manage_guild:
                send=send+':o:�T�[�o�[�̊Ǘ�\n'
            else:
                send=send+':x:�T�[�o�[�̊Ǘ�\n'
            if user.guild_permissions.view_audit_log:
                send=send+':o:�č����O�̕\��\n'
            else:
                send=send+':x:�č����O�̕\��\n'
            if user.guild_permissions.add_reactions:
                send=send+':o:���A�N�V�����̒ǉ�\n'
            else:
                send=send+':x:���A�N�V�����̒ǉ�\n'
            if user.guild_permissions.priority_speaker:
                send=send+':o:�D��X�s�[�J�[\n'
            else:
                send=send+':x:�D��X�s�[�J�[\n'
            if user.guild_permissions.stream:
                send=send+':o:�z�M\n'
            else:
                send=send+':x:�z�M\n'
            if user.guild_permissions.view_channel:
                send=send+':o:�`�����l��������\n'
            else:
                send=send+':x:�`�����l��������\n'
            if user.guild_permissions.read_message_history:
                send=send+':o:���b�Z�[�W������ǂ�\n'
            else:
                send=send+':x:���b�Z�[�W������ǂ�\n'
            if user.guild_permissions.send_messages:
                send=send+':o:���b�Z�[�W�̑��M\n'
            else:
                send=send+':x:���b�Z�[�W�̑��M\n'
            if user.guild_permissions.send_tts_messages:
                send=send+':o:tts�R�}���h�̎g�p\n'
            else:
                send=send+':x:tts�R�}���h�̎g�p\n'
            if user.guild_permissions.manage_messages:
                send=send+':o:���b�Z�[�W�̊Ǘ�\n'
            else:
                send=send+':x:���b�Z�[�W�̊Ǘ�\n'
            if user.guild_permissions.embed_links:
                send=send+':o:���ߍ��݃����N���g�p\n'
            else:
                send=send+':x:���ߍ��݃����N���g�p\n'
            if user.guild_permissions.attach_files:
                send=send+':o:�t�@�C���𑗐M\n'
            else:
                send=send+':x:�t�@�C���𑗐M\n'
            if user.guild_permissions.mention_everyone:
                send=send+':o:�S�Ẵ��[���Ƀ����V����\n'
            else:
                send=send+':x:�S�Ẵ��[���Ƀ����V����\n'
            if user.guild_permissions.use_external_emojis:
                send=send+':o:�O���̊G�����̎g�p\n'
            else:
                send=send+':x:�O���̊G�����̎g�p\n'
            if user.guild_permissions.use_external_stickers:
                send=send+':o:�O���̃X�^���v�̎g�p\n'
            else:
                send=send+':x:�O���̃X�^���v�̎g�p\n'
            if user.guild_permissions.view_guild_insights:
                send=send+':o:�T�[�o�[�C���T�C�g�̕\��\n'
            else:
                send=send+':x:�T�[�o�[�C���T�C�g�̕\��\n'
            if user.guild_permissions.connect:
                send=send+':o:�{�C�X�`�����l���ɐڑ�\n'
            else:
                send=send+':x:�{�C�X�`�����l���ɐڑ�\n'
            if user.guild_permissions.speak:
                send=send+':o:�{�C�X�`�����l���Ŕ���\n'
            else:
                send=send+':x:�{�C�X�`�����l���Ŕ���\n'
            if user.guild_permissions.mute_members:
                send=send+':o:�����o�[���~���[�g\n'
            else:
                send=send+':x:�����o�[���~���[�g\n'
            if user.guild_permissions.deafen_members:
                send=send+':o:�����o�[�̃X�s�[�J�[���~���[�g\n'
            else:
                send=send+':x:�����o�[�̃X�s�[�J�[���~���[�g\n'
            if user.guild_permissions.move_members:
                send=send+':o:�����o�[�̈ړ�\n'
            else:
                send=send+':x:�����o�[�̈ړ�\n'
            if user.guild_permissions.use_voice_activation:
                send=send+':o:�������o�̎g�p\n'
            else:
                send=send+':x:�������o�̎g�p\n'
            if user.guild_permissions.change_nickname:
                send=send+':o:�j�b�N�l�[���̕ύX\n'
            else:
                send=send+':x:�j�b�N�l�[���̕ύX\n'
            if user.guild_permissions.manage_nicknames:
                send=send+':o:�j�b�N�l�[���̊Ǘ�\n'
            else:
                send=send+':x:�j�b�N�l�[���̊Ǘ�\n'
            if user.guild_permissions.manage_permissions:
                send=send+':o:���[���̊Ǘ�\n'
            else:
                send=send+':x:���[���̊Ǘ�\n'
            if user.guild_permissions.manage_webhooks:
                send=send+':o:�E�F�u�t�b�N�̊Ǘ�\n'
            else:
                send=send+':x:�E�F�u�t�b�N�̊Ǘ�\n'
            if user.guild_permissions.manage_emojis_and_stickers:
                send=send+':o:�G�����̊Ǘ�\n'
            else:
                send=send+':x:�G�����̊Ǘ�\n'
            if user.guild_permissions.use_slash_commands:
                send=send+':o:�A�v���P�[�V�����R�}���h�̎g�p\n'
            else:
                send=send+':x:�A�v���P�[�V�����R�}���h�̎g�p\n'
            if user.guild_permissions.request_to_speak:
                send=send+':o:�X�s�[�J�[�Q�������N�G�X�g\n'
            else:
                send=send+':x:�X�s�[�J�[�Q�������N�G�X�g\n'
            if user.guild_permissions.manage_events:
                send=send+':o:�C�x���g�̊Ǘ�\n'
            else:
                send=send+':x:�C�x���g�̊Ǘ�\n'
            if user.guild_permissions.manage_threads:
                send=send+':o:�X���b�h�̊Ǘ�\n'
            else:
                send=send+':x:�X���b�h�̊Ǘ�\n'
            if user.guild_permissions.create_public_threads:
                send=send+':o:���J�X���b�h�̍쐬\n'
            else:
                send=send+':x:���J�X���b�h�̍쐬\n'
            if user.guild_permissions.create_private_threads:
                send=send+':o:����J�X���b�h�̍쐬\n'
            else:
                send=send+':x:����J�X���b�h�̍쐬\n'
            if user.guild_permissions.send_messages_in_threads:
                send=send+':o:�X���b�h�Ń��b�Z�[�W�𑗐M\n'
            else:
                send=send+':x:�X���b�h�Ń��b�Z�[�W�𑗐M\n'
            perms = discord.Embed(title=user.name+'#'+user.discriminator+'�̌���',description=send,color=self.bot.Color)
            rls = discord.Embed(title=user.name+'#'+user.discriminator+'�̃��[��',description=roles,color=self.bot.Color)
            ebds.append(rls)
            ebds.append(perms)
        alm = discord.AllowedMentions.none()
        await ctx.send(embeds=ebds,allowed_mentions=alm)
async def setup(bot):
    await bot.add_cog(infomation(bot))