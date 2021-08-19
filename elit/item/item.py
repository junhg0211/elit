from elit import ItemData
from util import database


class Item:
    type = 0
    name = '아무것도 아님'

    def __init__(self, amount: int, item_id: int):
        self.amount = amount
        self.item_data = ItemData(item_id)

    def set_amount(self, amount: int) -> 'Item':
        self.amount = amount
        with database.cursor() as cursor:
            cursor.execute('UPDATE inventory SET amount = %s WHERE item_id = %s', (self.amount, self.item_data.id))
        return self

    def __str__(self):
        return f'{self.type}: {self.name}'

    def __repr__(self):
        return f'{self} ({self.amount})'
