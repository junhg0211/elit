from typing import Optional, Tuple

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.item import Item
from util import eul_reul, const


class Check10(Item):
    name = '10원짜리 수표'
    type = 2
    description = f'10원짜리 수표입니다. ' \
                  f'사용하면 10{const("currency.default")}{eul_reul(const("currency.default"))} 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(10 * amount)
        return self.apply_use(amount, f'__{self.name}__{eul_reul(self.name)} __{amount}번__ 사용해서 '
                                      f'__{10 * amount}{currency}__{eul_reul(currency)} 얻었다!!'), None


class Check100(Item):
    name = '100원짜리 수표'
    type = 5
    description = f'100원짜리 수표입니다. ' \
                  f'사용하면 100{const("currency.default")}{eul_reul(const("currency.default"))} 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(100 * amount)
        return self.apply_use(amount, f'__{self.name}__{eul_reul(self.name)} __{amount}번__ 사용해서 '
                                      f'__{100 * amount}{currency}__{eul_reul(currency)} 얻었다!!'), None


class Check1000(Item):
    name = '1000원짜리 수표'
    type = 6
    description = f'1000원짜리 수표입니다. ' \
                  f'사용하면 1000{const("currency.default")}{eul_reul(const("currency.default"))} 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(1000 * amount)
        return self.apply_use(amount, f'__{self.name}__{eul_reul(self.name)} __{amount}번__ 사용해서 '
                                      f'__{1000 * amount}{currency}__{eul_reul(currency)} 얻었다!!'), None


class Check10000(Item):
    name = '10000원짜리 수표'
    type = 7
    description = f'10000원짜리 수표입니다. ' \
                  f'사용하면 10000{const("currency.default")}{eul_reul(const("currency.default"))} 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.check_amount(amount)
        currency = const("currency.default")
        player.earn_money(10000 * amount)
        return self.apply_use(amount, f'__{self.name}__{eul_reul(self.name)} __{amount}번__ 사용해서 '
                                      f'__{10000 * amount}{currency}__{eul_reul(currency)} 얻었다!!'), None
