from discord.ext.commands import Cog, Bot, command, Context, DefaultHelpCommand


class General(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.bot.help_command.command_attrs.update({'aliases': ['도움말']})
        bot.help_command = DefaultHelpCommand(command_attrs=self.bot.help_command.command_attrs)

    @command(aliases=['핑'],
             description='핑퐁! 핑(지연 시간)을 확인합니다.')
    async def ping(self, ctx: Context):
        await ctx.send(f':ping_pong: 핑퐁! (핑: {self.bot.latency * 1000:.3f}ms)')


def setup(bot: Bot):
    bot.add_cog(General(bot))
