from pymysql.cursors import DictCursor

from util import database


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


def get_data(id_: int):
    with database.cursor(DictCursor) as cursor:
        cursor.execute('SELECT * FROM item_data WHERE item_id = %s', id_)
        return cursor.fetchall()
