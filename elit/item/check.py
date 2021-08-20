from discord.ext.commands import Bot

from elit.item import Item
from util import eul_reul, const


class Check10(Item):
    name = '10원짜리 수표'
    type = 2

    def use(self, amount: int, player, bot: Bot) -> str:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(10 * amount)
        return self.apply_use(amount, f'{self.name}{eul_reul(self.name)} {amount}번 사용해서 '
                                      f'{10 * amount}{currency}{eul_reul(currency)} 얻었다!!')
