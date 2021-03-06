from math import inf
from typing import Tuple, Optional, Callable

from discord import Embed
from discord.ext.commands import Bot, Context

from elit import ItemData
from util import database, eul_reul, eun_neun, i_ga


class Item:
    type = 0
    name = '아무것도 아님'
    description = '아무것도 아닙니다'
    buy_prise = inf

    def __init__(self, item_id: int):
        self.item_data = ItemData(item_id)

        self.amount = self.get_amount()

    def __str__(self):
        return f'`{self.item_data.id}`: {self.name}'

    def __repr__(self):
        return f'{self} ({self.amount})'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        return self.apply_use(amount, f'`{self.name}`{eul_reul(self.name)} {amount}개 사용했다!'), None

    def get_fields(self) -> filter:
        return filter(lambda x: not x.startswith('__')
                      and x not in ('item_data', 'amount', 'type', 'description', 'name')
                      and not isinstance(getattr(self, x), Callable), dir(self))

    def set_amount(self, amount: int) -> 'Item':
        """
        아이템의 개수를 설정합니다.
        아이템의 개수가 0개로 설정되면 데이터베이스의 ``inventory`` 테이블 상에서 아이템을 제거합니다.

        :param amount: 설정할 아이템의 개수
        """
        self.amount = amount
        with database.cursor() as cursor:
            if self.amount:
                cursor.execute('UPDATE inventory SET amount = %s WHERE item_id = %s', (self.amount, self.item_data.id))
            else:
                cursor.execute('DELETE FROM inventory WHERE item_id = %s', self.item_data.id)
        return self

    def get_amount(self) -> Optional[int]:
        with database.cursor() as cursor:
            cursor.execute('SELECT amount FROM inventory WHERE item_id = %s', self.item_data.id)
            data = cursor.fetchall()
        if data:
            return data[0][0]

    def get_prise_per_piece(self) -> int:
        """
        아이템 하나 판매 시 가격을 반환합니다.

        :return: 아이템 한 개 판매 시 가격
        """
        return 0

    def apply_use(self, amount: int, use_message: str) -> str:
        self.set_amount(self.amount - amount)
        return use_message

    def check_amount(self, amount: int):
        """
        이 아이템을 `amount` 개 사용할 수 있는지 확인하고, 사용할 수 없다면 오류를 발생합니다.

        :exception ValueError: `amount`가 사용 가능 개수보다 많음
        """
        if self.amount < amount:
            raise ValueError(f':x: **{self.name}{eun_neun(self.name)} {self.amount}개까지 사용할 수 있습니다.**')


class Item1(Item):
    type = 1
    name = "아무것"
    description = '아무것입니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.check_amount(amount)
        return self.apply_use(amount, f'헉!! `{self.name}`{i_ga(self.name)} {amount}개!!'), None
