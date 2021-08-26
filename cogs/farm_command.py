from asyncio import TimeoutError as AsyncioTimeoutError, wait

from discord import Embed, User, DMChannel, Message
from discord.ext.commands import Cog, Bot, group, Context, command

from elit import Farm, next_farm_id, new_farm, get_player, get_farm_by_channel_id, get_farm_by_entrance_id
from elit.item import Crop
from util import const, emoji_reaction_check, eul_reul, i_ga, wa_gwa


def check_farm(ctx: Context, bot: Bot):
    player = get_player(ctx.author.id)
    if not player.is_in_farm():
        return f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 밭에 소속되어 있어야 해요!** ' \
               f'`엘 밭` 명령어를 통해 밭에 소속되는 방법을 알아보세요.'
    farm = Farm(player.farm_id)
    if ctx.channel.id in (farm.channel_id, farm.external_entrance_id):
        return False
    else:
        return f':park: {ctx.author.mention} **이 명령어를 사용하기 위해서는 자신이 소속되어있는 밭에 있어야 해요!** ' \
               f'{farm.get_channel(bot).mention}에서 시도해보세요.'


class FarmCommand(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message):
        if not message.content.startswith(':chains:'):
            if (farm := get_farm_by_channel_id(message.channel.id)) is not None:
                if farm.external_entrance_id is not None:
                    entrance_channel = self.bot.get_channel(farm.external_entrance_id)
                    await entrance_channel.send(f':chains: __{message.author.display_name}__: {message.content}',
                                                embed=message.embeds[0] if message.embeds else None,
                                                files=message.attachments)
            elif (farm := get_farm_by_entrance_id(message.channel.id)) is not None:
                farm_channel = self.bot.get_channel(farm.channel_id)
                await farm_channel.send(f':chains: __{message.author.display_name}__: {message.content}',
                                        embed=message.embeds[0] if message.embeds else None,
                                        files=message.attachments)

    @group(name='밭', aliases=['farm'], help='자신의 밭 정보를 확인합니다.', invoke_without_command=True)
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
            await ctx.send(f':park: {ctx.author.mention} **시스템 상 예상치 못한 오류가 발생했습니다.** '
                           '이 문제를 해결하기 위해서는 전문가가 있어야 합니다. 관리자에게 보고해주세요.')
            return

        owner = farm.get_owner(self.bot)
        farm_using = farm.get_using()
        members = [self.bot.get_user(member_id).display_name for member_id in farm.get_member_ids()]
        crop_names = list()
        for crop in farm.get_crops():
            crop_names.append(crop.name)

        embed = Embed(title='밭 정보', description=f'ID: {farm.id}', color=const('color.farm'))
        embed.add_field(name='채널', value=farm.get_channel(self.bot).mention)
        embed.add_field(name='소유자', value=owner.display_name)
        embed.add_field(name='용량', value=f'{farm_using}/{farm.size} ({farm_using / farm.size * 100:.2f}% 사용중)')
        embed.add_field(name='공동계좌', value=f'__{farm.money}{const("currency.default")}__')
        embed.add_field(name='인원', value=f'{farm.member_count()}/{farm.capacity}: {", ".join(members)}', inline=False)
        if (entrance_channel := farm.get_external_entrance_channel(self.bot)) is not None:
            embed.add_field(name='연결된 채널', value=f'{entrance_channel.guild.name} #{entrance_channel.name}')
        if crop_names:
            embed.add_field(name='심은 작물', value=', '.join(crop_names), inline=False)
        embed.set_thumbnail(url=owner.avatar_url)
        embed.set_footer(text='`엘 작물`을 통해서 밭에 심어져 있는 작물들에 대한 정보를 확인할 수 있습니다.')
        await ctx.send(embed=embed)

    @farm.command(name='생성', aliases=['create'], help='새로운 밭을 생성합니다.')
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

    @farm.command(name='나가기', aliases=['leave'], help='밭에서 나갑니다.')
    async def leave(self, ctx: Context):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        farm = player.get_farm()

        if farm.owner_id == ctx.author.id and farm.member_count() > 1:
            await ctx.send(f':people_wrestling: {ctx.author.mention} **밭에서 소유자가 나가기 위해서는 다른 구성원이 없어야 합니다!** ')
            return

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

    @farm.command(name='초대', aliases=['invite'], help='밭에 구성원을 초대합니다.')
    async def invite(self, ctx: Context, user: User):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        try:
            invitee = get_player(user.id)
        except ValueError:
            await ctx.send(f':people_wrestling: {ctx.author.mention} **__{user.display_name}__님의 정보를 확인할 수 없어요!** '
                           f'__{user.display_name}__님이 플레이어 정보를 생성하지 않아서 그래요. '
                           f'*`엘 돈`을 통해 플레이어 정보를 생성한 후에 다시 시도*해주세요.')
            return

        invitee_user = invitee.get_user(self.bot)
        if invitee.is_in_farm():
            await ctx.send(f':people_wrestling: {ctx.author.mention} '
                           f'**__{invitee_user.display_name}__님은 이미 가입한 밭이 있습니다!** '
                           f'밭을 탈퇴하기 위해서는 __{invitee_user.display_name}__님이 직접 `엘 밭 나가기` 명령어를 사용해주세요.')
            return

        farm = player.get_farm()

        if farm.member_count() >= farm.capacity:
            await ctx.send(f':people_wrestling: {ctx.author.mention} **밭 구성원이 가득 찼습니다!** '
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

    @farm.command(name='입금', aliases=['credit'], help='밭 공동계좌에 돈을 입금합니다.')
    async def credit(self, ctx: Context, amount: int):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)

        currency = const('currency.default')
        if player.money < amount:
            await ctx.send(f':moneybag: {ctx.author.mention} '
                           f'**충분히 돈을 가지고 있지 않아요!** __{amount}{currency}__{eul_reul(currency)} '
                           f'입금하기 위해서는 __{amount - player.money}{currency}__{i_ga(currency)} 더 필요해요!')
            return
        player.set_money(player.money - amount)

        farm = player.get_farm()
        previous_money = farm.money
        farm.set_money(farm.money + amount)

        await ctx.send(f':moneybag: {farm.get_channel(self.bot).mention}에 돈을 __{amount}{currency}__ 입금했습니다!\n'
                       f'> **이전 계좌 금액** __{previous_money}{currency}__\n'
                       f'> **현재 계좌 금액** __{farm.money}{currency}__\n'
                       f'> **입금한 금액** __{amount}{currency}__')

    @farm.command(name='출금', aliases=['인출', 'withdraw'], help='밭 공동계좌에서 돈을 인출합니다.')
    async def withdraw(self, ctx: Context, amount: int):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        farm = player.get_farm()

        currency = const('currency.default')
        if farm.money < amount:
            await ctx.send(f':moneybag: {ctx.author.mention} '
                           f'**계좌에 돈이 부족해요!** 계좌에 __{farm.money}{currency}__만큼이 있어요. '
                           f'__{amount}{currency}__{eul_reul(currency)} 인출하기에는 '
                           f'__{amount - farm.money}{currency}__{i_ga(currency)} 부족해요.')
            return

        previous_money = farm.money
        farm.set_money(farm.money - amount)
        player.set_money(player.money + amount)

        await ctx.send(f':moneybag: {farm.get_channel(self.bot).mention}의 공동계좌에서 돈을 '
                       f'__{amount}{currency}__ 인출했습니다!\n'
                       f'> **이전 계좌 금액** __{previous_money}{currency}__\n'
                       f'> **현재 계좌 금액** __{farm.money}{currency}__\n'
                       f'> **인출한 금액** __{amount}{currency}__')

    @farm.command(name='연결', aliases=['connect'], help='밭을 외부 서버와 연결합니다.')
    async def connect(self, ctx: Context):
        if ctx.channel.guild.id == const('guild.elitas'):
            await ctx.send(f':chains: {ctx.author.mention} **엘리타스 내부에서는 밭을 연결할 수 없어요!** '
                           f'`엘 연결`은 서버 밖의 채널에서 밭에 접근하기 위해서 사용합니다.')
            return

        if isinstance(ctx.channel, DMChannel):
            await ctx.send(f':chains: {ctx.author.mention} **DM 채널에는 밭을 연결할 수 없어요!**')
            return

        player = get_player(ctx.author.id)
        if not player.is_in_farm():
            await ctx.send(f':chains: {ctx.author.mention} **밭이 없어요!** '
                           f'연결할 밭이 없어요...')
            return

        farm = player.get_farm()

        # if farm.owner_id == ctx.author.id:
        #     await ctx.send(f':chains: {ctx.author.mention} **밭 소유자가 아니에요!** '
        #                    f'`엘 연결`은 밭의 소유자만 할 수 있습니다.')
        #     return
        
        if (connected_farm := get_farm_by_entrance_id(ctx.channel.id)) is not None:
            await ctx.send(f':chains: {ctx.author.mention} **연결 채널에 연결할 수 없습니다!** '
                           f'이 채널은 이미 __밭-{connected_farm.id}__{wa_gwa(str(connected_farm.id))} 연결되어 있습니다.')
            return

        farm_channel = farm.get_channel(self.bot)

        confirmation = await ctx.send(f':chains: 엘리타스의 __#{farm_channel.name}__{eul_reul(farm_channel.name)} '
                                      f'__{ctx.guild.name} {ctx.channel.mention}__에 연결하려고 합니다. '
                                      f'**밭이 연결되면 다음과 같은 일이 일어납니다**:\n'
                                      f'> 이 채널에서 입력된 모든 메시지가 엘리타스의 __{farm_channel.name}__ 채널에 전송됩니다.\n'
                                      f'> 엘리타스의 __{farm_channel.name}__ 채널에서 입력된 모든 메시지가 이 채널에 전송됩니다.\n'
                                      f'> 엘리타스의 __{farm_channel.name}__ 채널에 이 채널과 밭이 연결되었다는 메시지가 전송됩니다.\n'
                                      f'> 이 채널이 __{farm_channel.name}__의 다른 위치로 기록되어,'
                                      f' 이 채널에서 밭에 있는 것과 동일한 작업을 수행할 수 있습니다.\n'
                                      f'> `엘 연결취소`를 통해서 언제나 밭과 이 채널의 연결을 취소할 수 있습니다.\n'
                                      f'상기된 내용에 동의하신다면 {const("emoji.white_check_mark")}를 눌러주세요. '
                                      f'작업을 취소하려면 아무것도 하지 않으면 됩니다.')
        await confirmation.add_reaction(const("emoji.white_check_mark"))

        try:
            await self.bot.wait_for('reaction_add', timeout=60,
                                    check=emoji_reaction_check(confirmation, const('emoji.white_check_mark'),
                                                               ctx.author))
        except AsyncioTimeoutError:
            await confirmation.edit(content=f':chains: 시간이 초과되어 연결 작업이 취소되었습니다.')
            return

        farm.set_external_entrance_id(ctx.channel.id)
        await wait((
            ctx.send(f':chains: **{ctx.channel.mention}{i_ga(ctx.channel.name)} __{farm_channel.name}__에 연결되었습니다!**'),
            farm_channel.send(f':chains: __{ctx.guild.name}__의 __{ctx.channel.name}__ 채널이 '
                              f'{farm_channel.mention}{wa_gwa(farm_channel.name)} 연결되었습니다!')
        ))

    @farm.command(name='연결해제', aliases=['disconnect', '끊기'], help='외부 서버와의 연결을 끊습니다.')
    async def disconnect(self, ctx: Context):
        pass

    @group(name='작물', aliases=['농작물', 'crop'], help='밭에 심어진 작물 정보를 확인합니다.', invoke_without_command=True)
    async def crop(self, ctx: Context, *, crop_name: str = ''):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        farm = get_player(ctx.author.id).get_farm()

        if crop_name:
            crop = farm.get_planted_crop_by_name(crop_name)

            if crop is None:
                await ctx.send(f':potted_plant: {ctx.author.mention} **작물 정보를 확인할 수 없어요!** '
                               f'`{crop_name}`이라고 입력됐어요. 혹시 밭에 심어져있지 않은 작물은 아닌지 확인해주세요.')
                return

            await ctx.send(embed=crop.get_embed())
        else:
            farm_channel = farm.get_channel(self.bot)

            not_crop = True
            embed = Embed(title='밭에 심어져 있는 작물', description=farm_channel.mention, color=const('color.farm'))
            for crop in farm.get_crops():
                name, value = crop.get_simple_line()
                embed.add_field(name=name, value=value, inline=False)
                not_crop = False
            if not_crop:
                embed.add_field(name='(없음)', value='(없음)')
            embed.set_thumbnail(url=farm.get_owner(self.bot).avatar_url)
            embed.set_footer(text='`엘 작물 자세히`를 통해서 밭에 심어진 작물들에 대한 상세 정보를 확인할 수 있습니다.')
            await ctx.send(embed=embed)

    @crop.command(name='자세히', aliases=['specific'], help='작물 정보를 자세히 표시합니다.')
    async def specific(self, ctx: Context):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        farm = get_player(ctx.author.id).get_farm()
        farm_channel = farm.get_channel(self.bot)

        not_crop = True
        embed = Embed(title='밭 작물 자세히 보기', description=farm_channel.mention, color=const('color.farm'))
        for crop in farm.get_crops():
            name, value = crop.get_line()
            embed.add_field(name=name, value=value, inline=False)
            not_crop = False
        if not_crop:
            embed.add_field(name='(없음)', value='(없음)')
        embed.set_thumbnail(url=farm.get_owner(self.bot).avatar_url)
        embed.set_footer(text='`엘 작물 <작물 이름>`을 통해서 작물에 대한 상세 정보를 확인할 수 있습니다.')
        await ctx.send(embed=embed)

    @command(name='수확', aliases=['추수', 'harvest'], help='밭에 있는 작물을 수확합니다.')
    async def harvest(self, ctx: Context, *, crop_name: str):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        farm = player.get_farm()

        try:
            crop = farm.pull(crop_name)
        except ValueError:
            await ctx.send(f':potted_plant: {ctx.author.mention} **밭에 __{crop_name}__{i_ga(crop_name)} 심어져있지 않아요!** '
                           f'수확하려고 하는 작물의 이름이 `{crop_name}`이 맞는지 다시 한 번 확인해주세요.')
            return

        crop_item: Crop
        crop_item, amount = player.get_inventory().earn_item(4, crop.amount)
        crop_item.set_name(crop.name)
        crop_item.set_quality(crop.get_quality())

        await ctx.send(f':potted_plant: __{crop.name}__{eul_reul(crop.name)} __{amount}개__ 수확했습니다! '
                       f'(`{crop_item.item_data.id}`)')

    @command(name='뽑아내기', aliases=['pull', '뽑기'],
             help='밭에 심어져있는 작물을 뽑아냅니다. 뽑아낸 작물은 아이템을 드랍하지 않습니다.')
    async def pull(self, ctx: Context, *, crop_name: str):
        player = get_player(ctx.author.id)
        farm = player.get_farm()
        try:
            farm.pull(crop_name)
        except ValueError:
            await ctx.send(f':potted_plant: {ctx.author.mention} '
                           f'**밭에 __{crop_name}__{i_ga(crop_name)} 심어져있지 않아요!** '
                           f'뽑으려고 하는 작물의 이름이 `{crop_name}`이 맞는지 다시 한 번 확인해주세요.')
            return

        await ctx.send(f':eggplant: __{crop_name}__{eul_reul(crop_name)} 뽑아냈습니다.')


def setup(bot: Bot):
    bot.add_cog(FarmCommand(bot))
