from discord import TextChannel, User
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from util import database, const


def next_farm_id():
    with database.cursor() as cursor:
        # noinspection SqlResolve
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

    def get_channel(self, bot: Bot) -> TextChannel:
        return bot.get_channel(self.channel_id)

    def get_owner(self, bot: Bot) -> User:
        return bot.get_user(self.owner_id)

    def get_member_ids(self) -> list:
        with database.cursor() as cursor:
            cursor.execute('SELECT discord_id FROM player WHERE farm_id = %s', self.id)
            return [member[0] for member in cursor.fetchall()]

    def get_using(self):
        return 0

    def member_count(self) -> int:
        with database.cursor() as cursor:
            cursor.execute('SELECT discord_id FROM player WHERE farm_id = %s', self.id)
            return len(cursor.fetchall())

    async def check_empty(self, bot: Bot):
        if self.member_count():
            return

        farm_deprecated_category = bot.get_channel(const('category_channel.farm_deprecated'))
        farm_channel = bot.get_channel(self.channel_id)
        await farm_channel.edit(category=farm_deprecated_category, sync_permissions=True)

        await farm_channel.send(':people_wrestling: 밭에 사람이 아무도 없는 것이 확인되어 카테고리를 이동했습니다! '
                                '만약 이 밭의 구성원이 이 메시지를 보고 있다면 관리자를 호출해주세요. 밭을 복구해줄게요.')


def new_farm(farm_id: int, owner_id: int, channel_id: int) -> Farm:
    with database.cursor(DictCursor) as cursor:
        cursor.execute('INSERT INTO farm(farm_id, owner_id, channel_id) VALUES (%s, %s, %s)',
                       (farm_id, owner_id, channel_id))
    return Farm(farm_id)


if __name__ == '__main__':
    # farm = Farm(1)
    # print(farm.id, farm.money, farm.owner_id, farm.size, farm.channel_id)

    print(next_farm_id())
