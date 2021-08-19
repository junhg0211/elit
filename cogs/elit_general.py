from asyncio import wait, TimeoutError as AsyncioTimeoutError

from discord import User, Embed
from discord.ext.commands import Cog, Bot, group, Context, has_role, MissingRole, command

from elit import Player, new_player, get_money_leaderboard, Farm, next_farm_id, new_farm
from util import const, eul_reul, i_ga, na_ina, emoji_reaction_check


def check_farm(method):
    async def decorated(self, ctx: Context, *args, **kwargs):
        player = Player(ctx.author.id)
        if not player.has_farm():
            await ctx.send(f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 밭에 소속되어 있어야 해요!** '
                           f'`엘 밭` 명령어를 통해 밭에 소속되는 방법을 알아보세요.')
            return
        farm = Farm(player.farm_id)
        if ctx.channel.id == farm.channel_id:
            return await method(self, ctx, *args, **kwargs)
        else:
            await ctx.send(f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 자신이 소속되어있는 밭에 있어야 해요!** '
                           f'{farm.get_channel(self.bot).mention}에서 시도해보세요.')

    decorated.__name__ = method.__name__
    return decorated


class ElitGeneral(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=['info', '정보'],
             description='플레이어 정보를 확인합니다.')
    async def information(self, ctx: Context):
        try:
            player = Player(ctx.author.id)
        except ValueError:
            player = new_player(ctx.author.id)

        if player.has_farm():
            farm = Farm(player.farm_id)
        else:
            farm = None

        embed = Embed(title=f'**{ctx.author.display_name}**님의 정보', color=const('color.elit'))
        embed.add_field(name='서버 가입 일자', value=str(ctx.author.joined_at), inline=False)
        embed.add_field(name='소지금', value=f'{player.money}{const("currency.default")}')
        embed.add_field(name='소속되어있는 밭', value='(없음)' if farm is None else farm.get_channel(self.bot).mention)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

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

    @group(aliases=['밭'],
           description='자신의 밭 정보를 확인합니다.',
           invoke_without_command=True)
    async def farm(self, ctx: Context):
        try:
            player = Player(ctx.author.id)
        except ValueError:
            player = new_player(ctx.author.id)

        if player.farm_id is None:
            await ctx.send(f':park: **{ctx.author.mention}님이 소속한 밭이 존재하지 않습니다.**\n'
                           f'> - 밭을 가지고 있는 친구가 `엘 밭 초대` 명령어를 사용해서 *밭에 __{ctx.author.display_name}__님을 초대*하거나\n'
                           f'> - *본인 명의의 밭을 새로 만들 수* 있습니다. 본인 명의의 밭을 새로 만들기 위해서는 `엘 밭 생성`을 입력해주세요.')
            return

        try:
            farm = Farm(player.farm_id)
        except ValueError:
            await ctx.send(':park: **시스템 상 예상치 못한 오류가 발생했습니다.** '
                           '이 문제를 해결하기 위해서는 전문가가 있어야 합니다. 관리자에게 보고해주세요.')
            return

        await ctx.send(f'{farm.id, farm.channel_id, farm.owner_id, farm.size, farm.capacity}')

    @farm.command(aliases=['생성'],
                  description='새로운 밭을 생성합니다.')
    async def create(self, ctx: Context):
        try:
            player = Player(ctx.author.id)
        except ValueError:
            player = new_player(ctx.author.id)

        if player.farm_id is not None:
            confirmation = await ctx.send(
                f':park: **{ctx.author.mention}, 멈춰!!** '
                f'__{ctx.author.display_name}__님이 소속되어있는 밭이 이미 있습니다. '
                f'밭을 새로 만들면 이미 가입해있는 밭에서 탈퇴되고, 밭에 다시 초대밭을 때까지는 다시 밭에 가입할 수 없습니다. '
                f'만약 밭의 소유자라면 *영영 밭에 접근하지 못하게 될 수도 있습니다.* '
                f'계속 진행하시겠습니까?')
            await confirmation.add_reaction(const('emoji.white_check_mark'))

            try:
                await self.bot.wait_for('reaction_add',
                                        check=emoji_reaction_check(confirmation, const('emoji.white_check_mark'),
                                                                   ctx.author),
                                        timeout=30)
            except AsyncioTimeoutError:
                await confirmation.edit(content=':park: 제한 시간이 지나 확인이 취소되었습니다.')
                return

            await player.leave_farm(self.bot)

        farm_id = next_farm_id()
        farm_category = ctx.guild.get_channel(const('category_channel.farm'))
        farm_channel = await farm_category.create_text_channel(f'밭-{farm_id}')
        farm = new_farm(farm_id, ctx.author.id, farm_channel.id)
        await player.join(farm, self.bot)

        await ctx.send(f':park: {farm_channel.mention}{eul_reul(farm_channel.name)} 만들었습니다!')

    @farm.command(aliases=['나가기'],
                  description='밭에서 나갑니다.')
    @check_farm
    async def leave(self, ctx: Context):
        player = Player(ctx.author.id)
        farm = player.get_farm()
        farm_channel = farm.get_channel(self.bot)

        confirmation = await ctx.send(f':people_wrestling: 정말 {farm_channel.mention}에서 탈퇴하시겠습니까? '
                                      f'한 번 탈퇴한 밭으로는 다시 초대받을 때까지 가입할 수 없으며, '
                                      f'밭에 사람이 더 이상 남아있지 않다면 영영 접근하지 못할 수 있습니다. '
                                      f'계속하시려면 {const("emoji.white_check_mark")}를 눌러주세요.')
        await confirmation.add_reaction(const('emoji.white_check_mark'))

        try:
            await self.bot.wait_for('reaction_add',
                                    check=emoji_reaction_check(confirmation, const('emoji.white_check_mark'),
                                                               ctx.author),
                                    timeout=30)
        except AsyncioTimeoutError:
            await confirmation.edit(content=':people_wrestling: 시간이 초과되어 작업이 종료되었습니다.')
            return

        await wait((
            player.leave_farm(self.bot),
            ctx.send(f':people_wrestling: {farm_channel.mention}에서 탈퇴했습니다.')))

    @farm.command(aliases=['초대'],
                  description='밭에 구성원을 초대합니다.')
    async def invite(self, ctx: Context, user: User):
        pass

    @set.error
    async def set_error(self, ctx: Context, error):
        if isinstance(error, MissingRole):
            role = ctx.guild.get_role(const('role.enifia'))
            await ctx.send(f':spy: __{role}__ 역할을 가지고 있는 사람만 이 커맨드를 사용할 수 있어요!')


def setup(bot: Bot):
    bot.add_cog(ElitGeneral(bot))
