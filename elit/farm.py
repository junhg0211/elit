from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from util import database


def next_farm_id():
    with database.cursor() as cursor:
        cursor.execute('SELECT AUTO_INCREMENT '
                       'FROM information_schema.TABLES '
                       'WHERE TABLE_SCHEMA = "elit" AND TABLE_NAME = "farm"')
        return cursor.fetchall()[0][0]


class Farm:
    def __init__(self, id_: int):
        self.id = id_

        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT money, owner_id, `size`, channel_id, capacity FROM farm WHERE farm_id = %s', self.id)
            data = cursor.fetchall()
        if not data:
            raise ValueError('해당 ID를 가진 밭에 대한 정보가 존재하지 않습니다.')
        else:
            data = data[0]

        self.money = data['money']
        self.owner_id = data['owner_id']
        self.size = data['size']
        self.channel_id = data['channel_id']
        self.capacity = data['capacity']

    def get_channel(self, bot: Bot):
        return bot.get_channel(self.channel_id)

    def member_count(self) -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT discord_id FROM player WHERE farm_id = %s', self.id)
            return len(cursor.fetchall())


def new_farm(farm_id: int, owner_id: int, channel_id: int) -> Farm:
    with database.cursor(DictCursor) as cursor:
        cursor.execute('INSERT INTO farm(farm_id, owner_id, channel_id) VALUES (%s, %s, %s)',
                       (farm_id, owner_id, channel_id))
    return Farm(farm_id)


if __name__ == '__main__':
    # farm = Farm(1)
    # print(farm.id, farm.money, farm.owner_id, farm.size, farm.channel_id)

    print(next_farm_id())
