from typing import Union

from discord.ext.commands import Cog, Bot, command, Context

from elit import Player, get_item_object_by_id
from util import const, eul_reul, irago


def check_farm(ctx: Context, bot: Bot):
    shop_channel = bot.get_channel(const('text_channel.shop'))
    if ctx.channel != shop_channel:
        return f':shopping_cart: {ctx.author.mention} **이 명령어를 사용하기 위해서는 {shop_channel.mention}에 있어야 해요!**'
    return False


class Shop(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name='상점', aliases=['shop'], description='상점으로 이동합니다.')
    async def shop(self, ctx: Context):
        shop_channel = self.bot.get_channel(const('text_channel.shop'))

        if ctx.channel == shop_channel:
            await ctx.send(f':shopping_cart: 여기는 {shop_channel.mention}입니다!')
        else:
            await ctx.send(f':shopping_cart: {shop_channel.mention}에 가려면 이곳을 눌러주세요: {shop_channel.mention}')

    @command(name='판매', aliases=['sell'], description='아이템을 판매합니다.')
    async def sell(self, ctx: Context, item_id: int, amount: Union[int, str] = 1):
        if message := check_farm(ctx, self.bot):
            await ctx.send(message)
            return

        player = Player(ctx.author.id)
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


def setup(bot: Bot):
    bot.add_cog(Shop(bot))
