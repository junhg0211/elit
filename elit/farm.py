from datetime import datetime
from typing import Tuple, Optional

from discord import TextChannel, User
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from elit import Crop
from elit.exception import CropCapacityError
from util import database, const, eun_neun, i_ga


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
            cursor.execute('SELECT * FROM farm WHERE farm_id = %s', self.id)
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
        self.entrance_id = data['entrance_id']

    def get_channel(self, bot: Bot) -> TextChannel:
        return bot.get_channel(self.channel_id)

    def get_external_entrance_channel(self, bot: Bot) -> Optional[TextChannel]:
        if self.entrance_id is None:
            return
        if (channel := bot.get_channel(self.entrance_id)) is None:
            self.set_external_entrance_id(None)
            return
        return channel

    def set_external_entrance_id(self, channel_id: Optional[int]) -> 'Farm':
        if channel_id is None:
            self.channel_id = None
            with database.cursor() as cursor:
                cursor.execute('UPDATE farm SET entrance_id = NULL WHERE farm_id = %s', self.id)
            return self
        else:
            self.channel_id = channel_id
            with database.cursor() as cursor:
                cursor.execute('UPDATE farm SET entrance_id = %s WHERE farm_id = %s', (channel_id, self.id))
            return self

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

    def get_planted_crop_by_name(self, name: str) -> Optional[Crop]:
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

    def pull(self, crop_name: str) -> Crop:
        crop = self.get_planted_crop_by_name(crop_name)
        if crop is None:
            raise ValueError(f'밭에 {crop_name}{i_ga(crop_name)} 심어져있지 않습니다.')

        with database.cursor() as cursor:
            cursor.execute('DELETE FROM farm_crop WHERE crop_name = %s AND farm_id = %s', (crop_name, self.id))
        return crop

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

    def set_money(self, money: int) -> 'Farm':
        self.money = money
        if self.money < 0:
            raise ValueError('밭 계좌에는 0원 미만으로 가지고 있을 수 없습니다.')

        with database.cursor() as cursor:
            cursor.execute('UPDATE farm SET money = %s WHERE farm_id = %s', (self.money, self.id))
        return self


def new_farm(farm_id: int, owner_id: int, channel_id: int) -> Farm:
    with database.cursor(DictCursor) as cursor:
        cursor.execute('INSERT INTO farm(farm_id, owner_id, channel_id) VALUES (%s, %s, %s)',
                       (farm_id, owner_id, channel_id))
    return Farm(farm_id)


def get_farm_by_channel_id(channel_id: int) -> Optional[Farm]:
    with database.cursor() as cursor:
        cursor.execute('SELECT farm_id FROM farm WHERE channel_id = %s', channel_id)
        if not bool(data := cursor.fetchall()):
            return
    farm_id = data[0][0]
    return Farm(farm_id)


def get_farm_by_entrance_id(channel_id: int) -> Optional[Farm]:
    with database.cursor() as cursor:
        cursor.execute('SELECT farm_id FROM farm WHERE entrance_id = %s', channel_id)
        if not bool(data := cursor.fetchall()):
            return
    farm_id = data[0][0]
    return Farm(farm_id)
