from pymysql.cursors import DictCursor

from elit import get_item_object
from util import database


class Player:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id

        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT farm_id, money FROM player WHERE discord_id = %s', self.discord_id)
            data = cursor.fetchall()
        if not data:
            raise ValueError('해당 ID를 가진 플레이어에 대한 정보가 존재하지 않습니다.')
        else:
            data = data[0]

        self.farm_id = data['farm_id']
        self.money = data['money']
        self.player_inventory = PlayerInventory(self.discord_id)

    def set_money(self, amount: int):
        self.money = amount
        with database.cursor() as cursor:
            cursor.execute('UPDATE player SET money = %s WHERE discord_id = %s', (amount, self.discord_id))
        return self


class PlayerInventory:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id
        self.items = list()

        self.load_items()

    def __str__(self):
        return str(self.items)

    def load_items(self):
        with database.cursor() as cursor:
            cursor.execute('SELECT item_type, amount, item_id FROM inventory WHERE discord_id = %s', self.discord_id)
            items = cursor.fetchall()
        for item_type, amount, item_id in items:
            item = get_item_object(item_type, amount, item_id)
            if item is not None:
                self.items.append(item)
        return self


def new_player(discord_id: int) -> Player:
    with database.cursor() as cursor:
        cursor.execute('INSERT INTO player(discord_id, money) VALUES (%s, 0)', discord_id)
    return Player(discord_id)


def get_money_leaderboard(limit: int, from_: int = 0) -> tuple:
    """
    ``discord_id``, ``money``가 담겨있는 raw data가 다음과 같은 형태로 주어집니다.
    ``({'discord_id': ..., 'money': ...}, {'discord_id': ..., 'money': ...})``

    :param limit: 정보의 개수
    :param from_: 처음 정보 번째수
    :return:
    """
    with database.cursor(DictCursor) as cursor:
        cursor.execute('SELECT discord_id, money FROM player ORDER BY money DESC LIMIT %s, %s', (from_, limit))
        return cursor.fetchall()[from_:from_ + limit]
