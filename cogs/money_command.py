from asyncio import wait, TimeoutError as AsyncioTimeoutError

from discord import User, Embed
from discord.ext.commands import Cog, Bot, group, Context, has_role, MissingRole, command

from elit import Player, new_player, get_money_leaderboard, Farm
from util import const, eul_reul, i_ga, na_ina, emoji_reaction_check


class MoneyCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(aliases=['돈'],
           description='현재 가지고 있는 돈을 확인합니다.',
           invoke_without_command=True)
    async def money(self, ctx: Context):
        try:
            player = Player(ctx.author.id)
        except ValueError:
            player = new_player(ctx.author.id)
        await ctx.send(f':moneybag: __{ctx.author.display_name}__님의 소지금은 '
                       f'__{player.money}{const("currency.default")}__입니다.')

    @money.command(aliases=['보내기', '송금', '전송'],
                   description='다른 사람에게 돈을 전송합니다.')
    async def send(self, ctx: Context, user: User, amount: int):
        emoji = ':money_with_wings:'

        if ctx.author == user:
            await ctx.send(f'{emoji} **자기 자신에게는 송금할 수 없습니다!!**')
            return

        currency = const('currency.default')

        if amount <= 0:
            await ctx.send(f'{emoji} {ctx.author.mention} '
                           f'**0{currency}{na_ina(currency)} 0{currency}보다 적은 양은 송금할 수 없습니다!**')
            return

        try:
            sender = Player(ctx.author.id)
        except ValueError:
            sender = new_player(ctx.author.id)

        if sender.money < amount:
            await ctx.send(f'{emoji} {ctx.author.mention} **소지금이 부족합니다!**\n'
                           f'> **전송할 금액** {amount}{currency}\n'
                           f'> **소지금** {sender.money}{currency}\n'
                           f'> **추가로 필요한 금액** __{amount - sender.money}{const("currency.default")}__')
            return

        try:
            receiver = Player(user.id)
        except ValueError:
            await ctx.send(f'{emoji} **__{user.display_name}__님의 플레이어 정보를 확인할 수 없습니다!** '
                           f'{user.display_name}님이 돈을 받기 위해서는 '
                           f'`{const("command_prefix")[0]}{self.money.aliases[0]}` 커맨드를 통해 플레이어 정보를 생성해야 합니다. '
                           f'{ctx.author.mention}')
            return

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

    @money.command(aliases=['순위'],
                   description='소지금 순위를 확인합니다.')
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

    @money.command(aliases=['설정'],
                   description='소지금을 설정합니다.')
    @has_role(const('role.enifia'))
    async def set(self, ctx: Context, user: User, amount: int):
        try:
            player = Player(user.id)
        except ValueError as e:
            await ctx.send(str(e))
            return

        player.set_money(amount)
        await ctx.send(f':spy: __{user.display_name}__님의 소지금을 '
                       f'__{player.money}{const("currency.default")}__로 설정했습니다.')

    @set.error
    async def set_error(self, ctx: Context, error):
        if isinstance(error, MissingRole):
            role = ctx.guild.get_role(const('role.enifia'))
            await ctx.send(f':spy: __{role}__ 역할을 가지고 있는 사람만 이 커맨드를 사용할 수 있어요!')


def setup(bot: Bot):
    bot.add_cog(MoneyCog(bot))
