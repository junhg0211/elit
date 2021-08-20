from datetime import datetime
from typing import Tuple

from discord import TextChannel, User, Embed
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from elit.exception import CropCapacityError
from util import database, const, eun_neun


def next_farm_id():
    with database.cursor() as cursor:
        # noinspection SqlResolve
        cursor.execute('SELECT AUTO_INCREMENT '
                       'FROM information_schema.TABLES '
                       'WHERE TABLE_SCHEMA = "elit" AND TABLE_NAME = "farm"')
        return cursor.fetchall()[0][0]


class Crop:
    def __init__(self, farm_id: int, crop_name: str, amount: int, planted_at: datetime):
        self.farm_id = farm_id
        self.name = crop_name
        self.amount = amount
        self.planted_at = planted_at

    def get_embed(self) -> Embed:
        embed = Embed(title='작물 정보', color=const('color.crop'))
        embed.add_field(name='심은 날짜', value=str(self.planted_at), inline=False)
        embed.add_field(name='이름', value=self.name)
        embed.add_field(name='심은 개수', value=f'{self.amount}개')
        return embed


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

    def get_crops(self):
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM farm_crop WHERE farm_id = %s', self.id)
        for raw_crop in cursor.fetchall():
            yield Crop(self.id, raw_crop['crop_name'], raw_crop['amount'], raw_crop['planted_at'])

    def get_using(self) -> int:
        result = 0
        for crops in self.get_crops():
            result += crops.amount
        return result

    def get_planted_crop_by_name(self, name: str) -> Crop:
        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT * FROM farm_crop WHERE farm_id = %s AND crop_name = %s', (self.id, name))
            data = cursor.fetchall()
        if data:
            data = data[0]
            return Crop(self.id, name, data['amount'], data['planted_at'])

    def get_free_space(self) -> int:
        return self.size - self.get_using()

    def plant(self, name: str, amount: int) -> Tuple[int, datetime]:
        amount = min(amount, self.get_free_space())
        if amount <= 0:
            raise CropCapacityError('이 섬에 더 이상 작물을 심을 수 없습니다.')

        if self.get_planted_crop_by_name(name):
            raise ValueError(f'{name}{eun_neun(name)} 이미 심어져 있습니다.')
        else:
            with database.cursor() as cursor:
                cursor.execute('INSERT INTO farm_crop VALUES (%s, %s, %s, %s)',
                               (self.id, name, amount, planted_at := datetime.now()))
            return amount, planted_at

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
