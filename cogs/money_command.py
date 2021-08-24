from asyncio import wait, TimeoutError as AsyncioTimeoutError

from discord import User, Embed
from discord.ext.commands import Cog, Bot, group, Context, has_role, MissingRole, CommandError

from elit import get_money_leaderboard, get_player
from util import const, eul_reul, i_ga, ina, emoji_reaction_check


class MoneyCommand(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='돈', aliases=['money'], help='현재 가지고 있는 돈을 확인합니다.', invoke_without_command=True)
    async def money(self, ctx: Context):
        player = get_player(ctx.author.id)
        await ctx.send(f':moneybag: __{ctx.author.display_name}__님의 소지금은 '
                       f'__{player.money}{const("currency.default")}__입니다.')

    @money.command(name='보내기', aliases=['송금', '전송', 'send'], help='다른 사람에게 돈을 전송합니다.')
    async def send(self, ctx: Context, user: User, amount: int):
        emoji = ':money_with_wings:'

        if ctx.author == user:
            await ctx.send(f'{emoji} {ctx.author.mention} **자기 자신에게는 송금할 수 없습니다!!**')
            return

        currency = const('currency.default')

        if amount <= 0:
            await ctx.send(f'{emoji} {ctx.author.mention} '
                           f'**0{currency}{ina(currency)} 0{currency}보다 적은 양은 송금할 수 없습니다!**')
            return

        sender = get_player(ctx.author.id)

        if sender.money < amount:
            await ctx.send(f'{emoji} {ctx.author.mention} **소지금이 부족합니다!**\n'
                           f'> **전송할 금액** {amount}{currency}\n'
                           f'> **소지금** {sender.money}{currency}\n'
                           f'> **추가로 필요한 금액** __{amount - sender.money}{const("currency.default")}__')
            return

        receiver = get_player(user.id)

        confirmation = await ctx.send(f'{emoji} __{user.display_name}__님께 '
                                      f'__{amount}{currency}__{eul_reul(currency)} 보내시겠습니까?\n'
                                      f'> **현재 소지금** __{sender.money}{currency}__\n'
                                      f'> **보낸 후 소지금** __{sender.money - amount}{currency}__\n'
                                      f'송금을 진행하기 위해서는 아래 {const("emoji.money_with_wings")} 이모지를 눌러주세요. '
                                      f'송금을 취소하려면 아무런 반응을 하지 않으면 됩니다.')
        await confirmation.add_reaction(const('emoji.money_with_wings'))

        try:
            await self.bot.wait_for('reaction_add',
                                    check=emoji_reaction_check(confirmation, const('emoji.money_with_wings'),
                                                               ctx.author),
                                    timeout=30)
        except AsyncioTimeoutError:
            await confirmation.edit(content='제한 시간이 지나 송금이 취소되었습니다.')
            return

        sender.set_money(sender.money - amount)
        receiver.set_money(receiver.money + amount)
        tasks = (
            confirmation.edit(content=f'{emoji} __{user.display_name}__님께 성공적으로 돈을 전송했습니다!'),
            confirmation.remove_reaction(const('emoji.money_with_wings'), self.bot.user),
            confirmation.remove_reaction(const('emoji.money_with_wings'), ctx.author),
            user.send(f'{emoji} __{ctx.author.display_name}__님께서 돈을 보내셨습니다! '
                      f'__{amount}{currency}__{eul_reul(currency)} 받아서 소지금이 '
                      f'__{receiver.money}{currency}__{i_ga(currency)} 되었습니다.')
        )
        await wait(tasks)

    @money.command(name='순위', aliases=['leaderboard'], help='소지금 순위를 확인합니다.')
    async def leaderboard(self, ctx: Context):
        leaderboard = get_money_leaderboard(10)
        leaderboard_text = list()
        for i, leader_raw in enumerate(leaderboard):
            user = ctx.guild.get_member(leader_raw['discord_id'])
            if user is None:
                user = f'`ID: {leader_raw["discord_id"]}`'
            else:
                user = user.display_name
            leaderboard_text.append(f'{i + 1}위. **{user}** {leader_raw["money"]}{const("currency.default")}')
        embed = Embed(title='소지금 순위 (상위 10명)', description='\n'.join(leaderboard_text), color=const('color.elit'))
        await ctx.send(embed=embed)

    @has_role(const('role.enifia'))
    @money.command(name='설정', aliases=['set'], help='소지금을 설정합니다.', hidden=True)
    async def set(self, ctx: Context, user: User, amount: int):
        player = get_player(user.id).set_money(amount)
        await ctx.send(f':spy: __{user.display_name}__님의 소지금을 '
                       f'__{player.money}{const("currency.default")}__로 설정했습니다.')

    @set.error
    async def set_error(self, ctx: Context, error: CommandError):
        if isinstance(error, MissingRole):
            role = ctx.guild.get_role(const('role.enifia'))
            await ctx.send(f':spy: __{role}__ 역할을 가지고 있는 사람만 이 커맨드를 사용할 수 있어요!')


def setup(bot: Bot):
    bot.add_cog(MoneyCommand(bot))
