from discord.ext.commands import Bot, Context

from elit.item import Item
from util import eul_reul, const


class Check10(Item):
    name = '10원짜리 수표'
    type = 2
    description = f'10원짜리 수표입니다. ' \
                  f'사용하면 10{const("currency.default")}{eul_reul(const("currency.default"))} 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> str:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(10 * amount)
        return self.apply_use(amount, f'{self.name}{eul_reul(self.name)} {amount}번 사용해서 '
                                      f'{10 * amount}{currency}{eul_reul(currency)} 얻었다!!')
