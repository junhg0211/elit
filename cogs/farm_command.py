from asyncio import TimeoutError as AsyncioTimeoutError

from discord import Embed, User
from discord.ext.commands import Cog, Bot, group, Context

from elit import Farm, next_farm_id, new_farm, get_player
from util import const, emoji_reaction_check, eul_reul


def check_farm(ctx: Context, bot: Bot):
    player = get_player(ctx.author.id)
    if not player.is_in_farm():
        return f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 밭에 소속되어 있어야 해요!** ' \
               f'`엘 밭` 명령어를 통해 밭에 소속되는 방법을 알아보세요.'
    farm = Farm(player.farm_id)
    if ctx.channel.id == farm.channel_id:
        return False
    else:
        return f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 자신이 소속되어있는 밭에 있어야 해요!** ' \
               f'{farm.get_channel(bot).mention}에서 시도해보세요.'


class FarmCommand(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(aliases=['밭'],
           description='자신의 밭 정보를 확인합니다.',
           invoke_without_command=True)
    async def farm(self, ctx: Context):
        player = get_player(ctx.author.id)

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

        owner = farm.get_owner(self.bot)
        farm_using = farm.get_using()
        members = [self.bot.get_user(member_id).display_name for member_id in farm.get_member_ids()]
        embed = Embed(title='밭 정보', description=f'ID: {farm.id}', color=const('color.elit'))
        embed.add_field(name='채널', value=farm.get_channel(self.bot).mention)
        embed.add_field(name='소유자', value=owner.display_name)
        embed.add_field(name='인원', value=f'{farm.member_count()}/{farm.capacity}\n{", ".join(members)}', inline=False)
        embed.add_field(name='용량', value=f'{farm_using}/{farm.size} ({farm_using / farm.size * 100:.2f}% 사용중)',
                        inline=False)
        embed.set_thumbnail(url=owner.avatar_url)
        await ctx.send(embed=embed)

    @farm.command(aliases=['생성'],
                  description='새로운 밭을 생성합니다.')
    async def create(self, ctx: Context):
        player = get_player(ctx.author.id)

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
    async def leave(self, ctx: Context):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        farm = player.get_farm()
        farm_channel = farm.get_channel(self.bot)

        confirmation = await ctx.send(f':people_wrestling: 정말 {farm_channel.mention}에서 탈퇴하시겠습니까? '
                                      f'한 번 탈퇴한 밭으로는 다시 초대받을 때까지 가입할 수 없으며, '
                                      f'밭에 사람이 더 이상 남아있지 않다면 영영 접근하지 못할 수 있습니다.\n'
                                      f'> 계속하시려면 {const("emoji.white_check_mark")}를 눌러주세요.\n'
                                      f'> 아무것도 안 하면 30초 후에 탈퇴가 취소됩니다.')
        await confirmation.add_reaction(const('emoji.white_check_mark'))

        try:
            await self.bot.wait_for('reaction_add',
                                    check=emoji_reaction_check(confirmation, const('emoji.white_check_mark'),
                                                               ctx.author),
                                    timeout=30)
        except AsyncioTimeoutError:
            await confirmation.edit(content=':people_wrestling: 시간이 초과되어 작업이 중단되었습니다.')
            return

        await player.leave_farm(self.bot)

    @farm.command(aliases=['초대'],
                  description='밭에 구성원을 초대합니다.')
    async def invite(self, ctx: Context, user: User):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        try:
            invitee = get_player(user.id)
        except ValueError:
            await ctx.send(f':people_wrestling: **__{user.display_name}__님의 정보를 확인할 수 없어요!** '
                           f'__{user.display_name}__님이 플레이어 정보를 생성하지 않아서 그래요. '
                           f'*`엘 돈`을 통해 플레이어 정보를 생성한 후에 다시 시도*해주세요.')
            return

        invitee_user = invitee.get_user(self.bot)
        if invitee.is_in_farm():
            await ctx.send(f':people_wrestling: **__{invitee_user.display_name}__님은 이미 가입한 밭이 있습니다!** '
                           f'밭을 탈퇴하기 위해서는 __{invitee_user.display_name}__님이 직접 `엘 밭 나가기` 명령어를 사용해주세요.')
            return

        farm = player.get_farm()

        if farm.member_count() >= farm.capacity:
            await ctx.send(':people_wrestling: **밭 구성원이 가득 찼습니다!** '
                           '밭에 있는 사람을 내쫒거나, 상점에서 밭 최대 인원 주문서를 구매해서 사용해주세요.')
            return

        farm_channel = farm.get_channel(self.bot)
        confirmation = await ctx.send(f':people_wrestling: __{user.display_name}__님을 '
                                      f'{farm_channel.mention}으로 초대하시려면 아래 '
                                      f'{const("emoji.white_check_mark")}를 눌러주세요. 아무것도 안 하면 초대가 취소됩니다.')
        await confirmation.add_reaction(const("emoji.white_check_mark"))

        try:
            await self.bot.wait_for('reaction_add', timeout=30,
                                    check=emoji_reaction_check(
                                        confirmation, const('emoji.white_check_mark'), ctx.author))
        except AsyncioTimeoutError:
            await ctx.send(':people_wrestling: 시간이 초과되어 초대가 중단되었습니다.')
            return

        await confirmation.edit(content=f':people_wrestling: {invitee_user.mention}님에게 초대를 보냈습니다! '
                                        f'5분 안에 {invitee_user.display_name}님이 이 메시지에 '
                                        f'{const("emoji.white_check_mark")} 반응을 남기면 초대가 수락됩니다.')
        try:
            await self.bot.wait_for('reaction_add', timeout=300,
                                    check=emoji_reaction_check(
                                        confirmation, const('emoji.white_check_mark'), invitee_user))
        except AsyncioTimeoutError:
            await ctx.send(':people_wrestling: 시간이 초과되어 초대 수락이 중단되었습니다.')
            return

        await invitee.join(farm, self.bot)


def setup(bot: Bot):
    bot.add_cog(FarmCommand(bot))
