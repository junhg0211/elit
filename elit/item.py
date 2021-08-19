from math import inf

from pymysql.cursors import DictCursor

from util import database


def get_data(id_: int):
    with database.cursor(DictCursor) as cursor:
        cursor.execute('SELECT * FROM item_data WHERE item_id = %s', id_)
        return cursor.fetchall()


class ItemData:
    def __init__(self, id_: int):
        self.id = id_
        self.data = dict()

        self.load_data()

    def set_data(self, key: str, value):
        self.data[key] = value
        return self

    def get_data(self, key: str):
        return self.data[key]

    def save_data(self):
        with database.cursor() as cursor:
            cursor.execute('DELETE FROM item_data WHERE item_id = %s;', self.id)
            for key, value in self.data.items():
                cursor.execute('INSERT INTO item_data VALUES (%s, %s, %s);', (self.id, key, repr(value)))
        return self

    def load_data(self):
        data = get_data(self.id)
        for datum in data:
            self.data[datum['property_key']] = eval(datum['property_value'])
        return self


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


def get_item_object(item_type, amount, item_id) -> Item:
    if item_type == -1:
        pass
    else:
        return Item(amount, item_id)


def get_item_name_by_type(item_type: int) -> str:
    for variable in __dir:
        if not variable.startswith('__') and variable[0].upper() == variable[0]:
            item_class = eval(variable)
            if issubclass(item_class, Item) and item_class.type == item_type:
                return item_class.name


def get_max_type_number() -> int:
    max_ = -inf
    for variable in __dir:
        if not variable.startswith('__') and variable[0].upper() == variable[0]:
            item_class = eval(variable)
            if issubclass(item_class, Item):
                max_ = max(max_, item_class.type)
    return max_


__dir = dir()

if __name__ == '__main__':
    print(get_item_name_by_type(0))
    print(get_max_type_number())
