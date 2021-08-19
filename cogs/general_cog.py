from discord import Embed
from discord.ext.commands import Cog, Bot, command, Context, DefaultHelpCommand

from elit import Player, new_player, Farm
from util import const


class GeneralCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.bot.help_command.command_attrs.update({'aliases': ['도움말']})
        bot.help_command = DefaultHelpCommand(command_attrs=self.bot.help_command.command_attrs)

    @command(aliases=['info', '정보'],
             description='플레이어 정보를 확인합니다.')
    async def information(self, ctx: Context):
        try:
            player = Player(ctx.author.id)
        except ValueError:
            player = new_player(ctx.author.id)

        if player.is_in_farm():
            farm = Farm(player.farm_id)
        else:
            farm = None

        embed = Embed(title=f'**{ctx.author.display_name}**님의 정보', color=const('color.elit'))
        embed.add_field(name='서버 가입 일자', value=str(ctx.author.joined_at), inline=False)
        embed.add_field(name='소지금', value=f'{player.money}{const("currency.default")}')
        embed.add_field(name='소속되어있는 밭', value='(없음)' if farm is None else farm.get_channel(self.bot).mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @command(aliases=['핑'],
             description='핑퐁! 핑(지연 시간)을 확인합니다.')
    async def ping(self, ctx: Context):
        await ctx.send(f':ping_pong: 핑퐁! (핑: {self.bot.latency * 1000:.3f}ms)')


def setup(bot: Bot):
    bot.add_cog(GeneralCog(bot))
