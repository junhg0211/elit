from math import inf
from typing import Union

from discord import Embed
from discord.ext.commands import Cog, Bot, command, Context, group

from elit import get_item_object_by_id, get_player, get_item_class_by_type
from util import const, eul_reul, irago, eun_neun, euro, i_ga


def check_farm(ctx: Context, bot: Bot):
    shop_channel = bot.get_channel(const('text_channel.shop'))
    if ctx.channel != shop_channel:
        return f':shopping_cart: {ctx.author.mention} **이 명령어를 사용하기 위해서는 {shop_channel.mention}에 있어야 해요!**'
    return False


async def send_menu(ctx: Context, menu_name: str, *item_types: int):
    embed = Embed(title='상점', description=menu_name, color=const('color.elit'))
    currency = const('currency.default')
    for item_type in item_types:
        item_class = get_item_class_by_type(item_type)
        embed.add_field(name=f'`{item_class.type}`. {item_class.name} ({item_class.buy_prise}{currency})',
                        value=item_class.description, inline=False)
    await ctx.send(embed=embed)


class Shop(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name='상점', aliases=['shop'], description='상점으로 이동합니다.')
    async def shop(self, ctx: Context):
        shop_channel = self.bot.get_channel(const('text_channel.shop'))

        if ctx.channel == shop_channel:
            await ctx.send(f':shopping_cart: **여기는 {shop_channel.mention}입니다!** '
                           f'`엘 도움말 판매`, `엘 도움말 메뉴`를 통해서 커맨드 사용법에 대해서 알아보세요!')
        else:
            await ctx.send(f':shopping_cart: {shop_channel.mention}에 가려면 이곳을 눌러주세요: {shop_channel.mention}')

    @command(name='판매', aliases=['sell'], description='아이템을 판매합니다.')
    async def sell(self, ctx: Context, item_id: int, amount: Union[int, str] = 1):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = get_player(ctx.author.id)
        inventory = player.get_inventory()

        if not inventory.has_item(item_id):
            await ctx.send(f':coin: {ctx.author.mention} **아이템을 가지고 있지 않아요!!** '
                           f'아이템 아이디가 `{item_id}`{irago(str(item_id))} 입력됐어요! 아이디를 틀리지 않게 잘 입력했나 확인해보세요.')
            return

        item = get_item_object_by_id(item_id)

        if amount in const('all_word'):
            amount = item.amount

        if isinstance(amount, str):
            check_gae = ' 혹시 숫자 뒤에 `개`를 붙이지 않았는지 확인해주세요!' if amount.endswith('개') else ''
            await ctx.send(f':coin: {ctx.author.mention} **올바른 개수를 입력해주세요!!** '
                           f'판매할 개수를 `{amount}`개라고 입력하셨어요.{check_gae}')
            return

        prise = item.get_prise_per_piece() * amount
        item.set_amount(item.amount - amount)

        player.earn_money(prise)

        currency = const("currency.default")
        await ctx.send(f':coin: __{item.name}__{eul_reul(item.name)} 팔고 __{prise}{currency}__{eul_reul(currency)} '
                       f'얻었습니다!')

    @command(name='구매', aliases=['buy'],
             description='아이템을 구매합니다.')
    async def buy(self, ctx: Context, item_type: int, amount: int = 1):
        player = get_player(ctx.author.id)
        item_class = get_item_class_by_type(item_type)

        if item_class is None:
            await ctx.send(f':shopping_cart: {ctx.author.mention} **아이템 정보를 확인할 수 없어요!** '
                           f'아이템 정보를 `{item_type}`이라고 입력했어요. 혹시 잘못 입력하지는 않았는지 확인해주세요.')
            return

        if item_class.buy_prise == inf:
            await ctx.send(f':shopping_cart: {ctx.author.mention} **비매품이에요!** '
                           f'`{item_class.name}`{eun_neun(item_class.name)} 비매품이기 때문에 상점에서 구매할 수 없어요.')
            return

        currency = const('currency.default')

        if player.money < (buy_prise := item_class.buy_prise * amount):
            await ctx.send(f':shopping_cart: {ctx.author.mention} **돈이 부족해요!!** '
                           f'`{item_class.name}`{eun_neun(item_class.name)} 한 개에 '
                           f'__{item_class.buy_prise}{currency}__{euro(currency)}, '
                           f'__{amount} 개__를 사려면 __{buy_prise}{currency}__{i_ga(currency)} 필요해요.')
            return

        item, amount = player.set_money(player.money - buy_prise).get_inventory().earn_item(item_type, amount)
        await ctx.send(f':shopping_cart: __{buy_prise}{currency}__{eul_reul(currency)} 주고 '
                       f'__{item.name}__{eul_reul(item.name)} __{amount} 개__ 구매했습니다!')

    @group(name='메뉴', aliases=['menu', '구매목록'],
           description='구매 가능한 아이템 목록을 확인합니다.',
           invoke_without_command=True)
    async def menu(self, ctx: Context):
        await ctx.send(f':shopping_cart: {ctx.author.mention} **구매 가능 아이템 목록을 확인해보세요!** '
                       f'구매할 수 있는 아이템의 타입은 `엘 메뉴 일반`, `엘 메뉴 농사` 등 서브커맨드를 통해 알아볼 수 있습니다. '
                       f'서브커맨드의 목록을 확인하려면 `엘 도움말 메뉴`를 입력해주세요!')
        return

    @menu.command(name='일반', aliases=['general', '기타'],
                  description='기타 아이템 목록을 확인합니다.')
    async def general(self, ctx: Context):
        await send_menu(ctx, '일반', 2, 5, 6, 7)

    @menu.command(name='농사', aliases=['farming'],
                  description='농사 아이템 목록을 확인합니다.')
    async def farming(self, ctx: Context):
        await send_menu(ctx, '농사', 3)


def setup(bot: Bot):
    bot.add_cog(Shop(bot))
