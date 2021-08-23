from typing import Union

from discord import User, Embed
from discord.ext.commands import Cog, Bot, group, Context, has_role, CommandError, MissingRole, command

from elit import get_player, get_item_class_by_type, get_max_type_number, get_item_name_by_type, get_item_object_by_id
from elit.exception import InventoryCapacityError
from util import const, eul_reul


class InventoryCommand(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group(name='인벤토리', aliases=['인벤', 'inventory', 'inv'], description='자신의 인벤토리를 확인합니다.',
           invoke_without_command=True)
    async def inventory(self, ctx: Context):
        player = get_player(ctx.author.id)
        inventory = player.get_inventory()
        embed = Embed(title='인벤토리', description=ctx.author.display_name, color=const('color.elit'))
        inventory_capacity = inventory.get_capacity()
        embed.add_field(name='용량', value=f'{inventory_capacity}/{inventory.size} '
                                         f'({inventory_capacity / inventory.size * 100:.2f}%)')
        embed.add_field(name='소지금', value=f'{player.money}{const("currency.default")}')
        embed.add_field(name='구성품', value=str(inventory) if inventory else '(없음)', inline=False)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text='`엘 아이템 <아이템 ID>`를 통해서 아이템에 대한 상세 정보를 확인할 수 있습니다.')
        await ctx.send(embed=embed)

    @command(name='타입', aliases=['type'], description='아이템 타입 목록을 확인합니다.')
    async def type(self, ctx: Context, type_number: int = -1):
        if type_number == -1:
            embed = Embed(title='사용 가능한 아이템 타입 목록', color=const('color.elit'))
            for type_number in range(get_max_type_number() + 1):
                if (item_class := get_item_class_by_type(type_number)) is not None:
                    embed.add_field(name=f'`{type_number}`: {item_class.name}',
                                    value=item_class.description, inline=False)
        else:
            item_type = get_item_class_by_type(type_number)
            embed = Embed(title='아이템 정보', description=item_type.name, color=const('color.elit'))
            embed.add_field(name='ID', value=item_type.type)
            embed.add_field(name='설명', value=item_type.description, inline=False)
            fields = '`' + '`, `'.join(item_type(0).get_fields()) + '`'
            if fields != '``':
                embed.add_field(name='데이터 키', value=fields)
        await ctx.send(embed=embed)

    @command(name='사용', aliases=['use'], description='아이템을 사용합니다.')
    async def use(self, ctx: Context, item_id: int, count: Union[int, str] = 1):
        player = get_player(ctx.author.id)
        inventory = player.get_inventory()
        item = get_item_object_by_id(item_id)

        if item is None:
            await ctx.send(f':roll_of_paper: {ctx.author.mention} **아이템 정보를 확인할 수 없습니다!** '
                           f'아이템 번호를 잘 입력했는지 확인해주세요.')
            return

        if not inventory.has_item(item_id):
            await ctx.send(f':roll_of_paper: '
                           f'**{ctx.author.mention}님은 `{item.name}`{eul_reul(item.name)} 가지고 있지 않아요!**')
            return

        if count in const('all_word'):
            count = item.amount

        try:
            log, embed = await player.use(item, count, self.bot, ctx)
        except Exception as e:
            log = str(e)
            embed = None
        await ctx.send(f':roll_of_paper: {ctx.author.display_name}: {log}', embed=embed)

    @command(name='아이템', aliases=['item'], description='아이템 정보를 확인합니다.')
    async def item(self, ctx: Context, item_id: int):
        player_inventory = get_player(ctx.author.id).get_inventory()

        if not player_inventory.has_item(item_id):
            await ctx.send(f':squeeze_bottle: **{ctx.author.mention}님은 이 아이템을 가지고 있지 않아요!** '
                           f'이 명령어는 가지고 있는 아이템에 대해서만 사용할 수 있어요.')
            return

        item = get_item_object_by_id(item_id)

        multiple_prise = f' (총 {item.get_prise_per_piece() * item.amount}{const("currency.default")})' \
            if item.amount != 1 else ''

        embed = Embed(title='아이템 정보', description=item.name, color=const('color.elit'))
        embed.add_field(name='ID', value=str(item.item_data.id))
        embed.add_field(name='소유자', value=ctx.author.display_name)
        embed.add_field(name='아이템 타입', value=f'{get_item_class_by_type(item.type).name} ({item.type})')
        embed.add_field(name='아이템 이름', value=str(item.name))
        embed.add_field(name='개수', value=f'{item.amount}개')
        embed.add_field(name='아이템 판매 시 가격',
                        value=f'{item.get_prise_per_piece()}{const("currency.default")}/개{multiple_prise}')
        embed.set_thumbnail(url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @has_role(const('role.enifia'))
    @command(name='주기', aliases=['give'], description='아이템을 줍니다.', hidden=True)
    async def give(self, ctx: Context, user: User, item_type: int, amount: int = 1):
        if not get_item_name_by_type(item_type):
            await ctx.send(f':baggage_claim: {ctx.author.mention} **아이템 정보를 확인할 수 없습니다!** '
                           f'아이템 타입 번호를 잘 입력했는지 확인해주세요.')
            return

        try:
            item, amount = get_player(user.id).get_inventory().earn_item(item_type, amount)
        except InventoryCapacityError:
            await ctx.send(f':baggage_claim: **__{user.display_name}__님의 인벤토리가 가득 찼습니다!!** '
                           f'더 이상 아이템을 받을 수 없습니다.')
        else:
            await ctx.send(f':baggage_claim: __{user.display_name}__님에게 '
                           f'__{get_item_name_by_type(item_type)} {amount}개__를 주었습니다! '
                           f'아이템의 아이디는 `{item.item_data.id}`입니다.')

    @give.error
    async def give_error(self, ctx: Context, error: CommandError):
        if isinstance(error, MissingRole):
            role = ctx.guild.get_role(const('role.enifia'))
            await ctx.send(f':baggage_claim: 이 커맨드를 사용하려면 __{role.name}__ 역할이 있어야 돼요!')


def setup(bot: Bot):
    bot.add_cog(InventoryCommand(bot))
