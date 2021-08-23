import traceback
from datetime import datetime

from discord import Embed
from discord.ext.commands import Cog, Bot, command, Context, DefaultHelpCommand, CommandError, \
    MissingRequiredArgument, CommandNotFound, BadArgument

from elit import Player, new_player, Farm
from util import const, eun_neun


class General(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.bot.help_command.command_attrs.update({
            'name': '도움말',
            'aliases': ['help'],
            'description': '명령어 목록을 보고 도움말을 표시합니다.',
            'help': ''
        })
        bot.help_command = DefaultHelpCommand(command_attrs=self.bot.help_command.command_attrs)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):
        print_log = False
        if isinstance(error, MissingRequiredArgument):
            print_log = True
            await ctx.send(f':x: **커맨드 구문을 놓쳤습니다!** 커맨드를 구문에 맞게 입력했는지 확인해주세요. '
                           f'커맨드 구문을 확인하려면 `엘 도움말 {ctx.command}`를 사용할 수도 있습니다.')
        elif isinstance(error, CommandNotFound):
            await ctx.send(f':x: **없는 커맨드입니다!** '
                           f'커맨드 이름에 오타가 나지는 않았는지 확인해주세요. '
                           f'`엘 도움말`을 사용하면 명령어 목록을 확인할 수 있습니다.')
        elif isinstance(error, BadArgument):
            print_log = True
            await ctx.send(f':x: **값의 형식이 틀렸습니다!** '
                           f'숫자를 입력하는 칸에 단어를 입력하지는 않았는지, 정수를 입력하는 칸에 소숫점이 포함된 숫자를 입력하지는 않았는지 등, '
                           f'커맨드에 입력한 값의 형식이 올바른지 확인해주세요.')
        else:
            print_log = True
            await ctx.send(f':x: **처리되지 않은 오류가 발생했습니다!** '
                           f'개발자도 이 오류가 발생할 것으로 예상하지 못했어요... 당장!! 개발자에게 이 사실을 알려주세요.')
        if print_log:
            print(f'{datetime.now()} `{ctx.guild} #{ctx.channel}`에서 오류 발생이 감지되었습니다.\n'
                  f'\t메시지 내용: {repr(ctx.message.content)}')
            traceback.print_exception(error.__class__, error, error.__traceback__)

    @command(name='정보', aliases=['info', 'information'], description='플레이어 정보를 확인합니다.')
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
        embed.add_field(name='소지금', value=f'__{player.money}{const("currency.default")}__')
        embed.add_field(name='소속되어있는 밭', value='(없음)' if farm is None else farm.get_channel(self.bot).mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @command(name='핑', aliases=['ping'], description='핑퐁! 핑(지연 시간)을 확인합니다.')
    async def ping(self, ctx: Context):
        await ctx.send(f':ping_pong: 핑퐁! (핑: {self.bot.latency * 1000:.3f}ms)')


def setup(bot: Bot):
    bot.add_cog(General(bot))
