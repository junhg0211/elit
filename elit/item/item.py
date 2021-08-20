from discord.ext.commands import Bot

from elit import ItemData
from util import database, eul_reul, eun_neun, i_ga


class Item:
    type = 0
    name = '아무것도 아님'

    def __init__(self, amount: int, item_id: int):
        self.amount = amount
        self.item_data = ItemData(item_id)

    def set_amount(self, amount: int) -> 'Item':
        self.amount = amount
        with database.cursor() as cursor:
            if self.amount:
                cursor.execute('UPDATE inventory SET amount = %s WHERE item_id = %s', (self.amount, self.item_data.id))
            else:
                cursor.execute('DELETE FROM inventory WHERE item_id = %s', self.item_data.id)
        return self

    def use(self, amount: int, player, bot: Bot) -> str:
        self.check_amount(amount)
        return self.apply_use(amount, f'`{self.name}`{eul_reul(self.name)} {amount}개 사용했다!')

    def apply_use(self, amount: int, use_message: str) -> str:
        self.set_amount(self.amount - amount)
        return use_message

    def check_amount(self, amount: int):
        """
        :exception ValueError: `amount`가 사용 가능 개수보다 많음
        """
        if self.amount < amount:
            raise ValueError(f':x: **{self.name}{eun_neun(self.name)} {self.amount}개까지 사용할 수 있습니다.**')

    def __str__(self):
        return f'`{self.type}`: {self.name}'

    def __repr__(self):
        return f'{self} ({self.amount})'


class Item1(Item):
    type = 1
    name = "아무것"

    def use(self, amount: int, player, bot: Bot) -> str:
        self.check_amount(amount)
        return self.apply_use(amount, f'헉!! `{self.name}`{i_ga(self.name)} {amount}개!!')