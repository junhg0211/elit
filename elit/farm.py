from pymysql.cursors import DictCursor

from util import database


class Farm:
    def __init__(self, id_: int):
        self.id = id_

        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT money, owner_id, `size`, channel_id FROM farm WHERE farm_id = %s', self.id)
            data = cursor.fetchall()
        if not data:
            raise ValueError('해당 ID를 가진 밭에 대한 정보가 존재하지 않습니다.')
        else:
            data = data[0]

        self.money = data['money']
        self.owner_id = data['owner_id']
        self.size = data['size']
        self.channel_id = data['channel_id']


if __name__ == '__main__':
    farm = Farm(1)
    print(farm.id, farm.money, farm.owner_id, farm.size, farm.channel_id)
