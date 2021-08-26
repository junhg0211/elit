from datetime import datetime, timedelta
from hashlib import md5
from math import exp
from random import seed, random
from typing import Tuple, Optional

from discord import TextChannel, User, Embed
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from elit.exception import CropCapacityError
from util import database, const, eun_neun, linear, cubic, i_ga


def next_farm_id():
    with database.cursor() as cursor:
        # noinspection SqlResolve
        cursor.execute('SELECT AUTO_INCREMENT '
                       'FROM information_schema.TABLES '
                       'WHERE TABLE_SCHEMA = "elit" AND TABLE_NAME = "farm"')
        return cursor.fetchall()[0][0]


def get_crop_duration(crop_name: str) -> timedelta:
    days = 0.3 * 1.35 ** len(crop_name)
    seed(int(md5(crop_name.encode()).hexdigest(), 16))
    multiplication = linear(random(), 0, 1, 0.1, 2)
    return timedelta(days=days * multiplication)


def get_grade(crop_name: str) -> int:
    """
    작물의 등급을 결정합니다.

    확률 분포:
      1 - 0: SS - duration 후 30일동안 썩지 않음
     10 - 1: S  - duration 후 15일동안 썩지 않음
     25 - 2: A  - duration 후 7일동안 썩지 않음
     50 - 3: B  - duration 후 3일동안 썩지 않음
    100 - 4: C  - duration 후 1일동안 썩지 않음
    150 - 5: D  - duration 후 6시간만에 썩음
    190 - 6: E  - duration 후 3시간만에 썩음
    200 - 7: F  - duration 후 1시간만에 썩음
    """

    a = int(md5(crop_name.encode()).hexdigest(), 16) % 200 + 1
    if a <= 1:
        return 0
    elif a <= 10:
        return 1
    elif a <= 25:
        return 2
    elif a <= 50:
        return 3
    elif a <= 100:
        return 4
    elif a <= 150:
        return 5
    elif a <= 190:
        return 6
    else:
        return 7


def get_grade_duration(grade: int) -> timedelta:
    return (
        timedelta(days=30),
        timedelta(days=15),
        timedelta(days=7),
        timedelta(days=3),
        timedelta(days=1),
        timedelta(seconds=21600),
        timedelta(seconds=10800),
        timedelta(seconds=3600),
    )[grade]


def get_grade_name(grade: int):
    return ('SS', 'S', 'A', 'B', 'C', 'D', 'E', 'F')[grade]


def get_prise(crop_name: str) -> int:
    duration = get_crop_duration(crop_name)
    return (duration.days * 86400 + duration.seconds) // 5000


class Crop:
    def __init__(self, farm_id: int, crop_name: str, amount: int, planted_at: datetime):
        self.farm_id = farm_id
        self.name = crop_name
        self.amount = amount
        self.planted_at = planted_at

    def get_duration(self) -> timedelta:
        return get_crop_duration(self.name)

    def get_grade(self) -> int:
        return get_grade(self.name)

    def get_grade_name(self) -> str:
        return get_grade_name(self.get_grade())

    def get_grade_duration(self) -> timedelta:
        return get_grade_duration(self.get_grade())

    def get_prise(self) -> int:
        return round(self.get_maximum_prise() * self.get_quality())

    def get_maximum_prise(self) -> int:
        return int(get_prise(self.name)) * self.amount

    def get_quality(self):
        now = datetime.now()

        crop_grown = self.planted_at + self.get_duration()
        crop_sustain_until = crop_grown + self.get_grade_duration()

        if now < crop_grown:
            return cubic(now, self.planted_at, crop_grown, 0, 1)
        elif now < crop_sustain_until:
            return 1
        else:
            delta = (now - crop_sustain_until)
            delta = delta.days + delta.seconds / 86400
            return exp(-10 * delta) * (10 * delta + 1)

    def quality_derivative_emoji(self):
        now = datetime.now()

        crop_grown = self.planted_at + self.get_duration()
        crop_sustain_until = crop_grown + self.get_grade_duration()

        if now < crop_grown:
            return ':arrow_up:'
        elif now < crop_sustain_until:
            return ':record_button:'
        else:
            return ':arrow_down:'

    def get_simple_line(self) -> Tuple[str, str]:
        if datetime.now() < (good_from := self.planted_at + self.get_duration()):
            value = f'{good_from}부터'
        else:
            value = f'{good_from + self.get_grade_duration()}까지'
        name = f'__{self.name}__({get_grade_name(self.get_grade())}) ⨉ {self.amount} ' \
               f'({self.get_quality() * 100:.2f}% {self.quality_derivative_emoji()},' \
               f' {self.get_prise()} / {self.get_maximum_prise()})'
        return name, value

    def get_line(self) -> Tuple[str, str]:
        now = datetime.now()
        if now < (good_from := self.planted_at + self.get_duration()):
            good_quality = f'{good_from}부터'
        else:
            good_quality = f'{good_from + self.get_grade_duration()}까지'

        name = f'__{self.name}__, {self.amount}개'
        value = f'- **심은 날짜**: {self.planted_at}\n' \
                f'- **작물 등급**: **{self.get_grade_name()}** ({self.get_grade_duration()})\n' \
                f'- **최상 품질**: {good_quality}\n' \
                f'- **현재 가격**: __{self.get_prise()}{const("currency.default")}__\n' \
                f'- **현재 품질**: __{self.get_quality() * 100:.2f}%__ {self.quality_derivative_emoji()}'
        return name, value

    def get_embed(self) -> Embed:
        embed = Embed(title='작물 정보', color=const('color.crop'))
        embed.add_field(name='이름', value=self.name)
        embed.add_field(name='심은 개수', value=f'{self.amount}개')
        embed.add_field(name='현재 품질', value=f'__{self.get_quality() * 100:.2f}%__ {self.quality_derivative_emoji()}')
        embed.add_field(name='심은 날짜', value=str(self.planted_at))
        embed.add_field(name='현재 가격', value=f'{self.get_prise()}{const("currency.default")}')
        embed.add_field(name='최고 가격', value=f'{self.get_maximum_prise()}{const("currency.default")}')
        embed.add_field(name='작물 등급', value=f'**{self.get_grade_name()}** (익은 후 {self.get_grade_duration()}간 최상 품질)',
                        inline=False)
        embed.add_field(name='최상 품질 재배 기간',
                        value=f'심은 시각부터 {self.get_duration()}:\n'
                              f'{self.planted_at + self.get_duration()}부터\n'
                              f'{self.planted_at + self.get_duration() + self.get_grade_duration()}까지', inline=False)
        embed.set_footer(text='`엘 작물`을 통해서 밭에 심어져있는 작물 목록을 한 번에 확인할 수 있습니다.')
        return embed


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
        self.external_entrance_id = data['external_entrance_id']

    def get_channel(self, bot: Bot) -> TextChannel:
        return bot.get_channel(self.channel_id)

    def get_external_entrance_channel(self, bot: Bot) -> Optional[TextChannel]:
        if self.external_entrance_id is None:
            return
        if (channel := bot.get_channel(self.external_entrance_id)) is None:
            self.set_external_entrance_id(None)
            return
        return channel

    def set_external_entrance_id(self, channel_id: Optional[int]) -> 'Farm':
        if channel_id is None:
            self.channel_id = None
            with database.cursor() as cursor:
                cursor.execute('UPDATE farm SET external_entrance_id = NULL WHERE farm_id = %s', self.id)
            return self
        else:
            self.channel_id = channel_id
            with database.cursor() as cursor:
                cursor.execute('UPDATE farm SET external_entrance_id = %s WHERE farm_id = %s', (channel_id, self.id))
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
        cursor.execute('SELECT farm_id FROM farm WHERE external_entrance_id = %s', channel_id)
        if not bool(data := cursor.fetchall()):
            return
    farm_id = data[0][0]
    return Farm(farm_id)


if __name__ == '__main__':
    # crop_name_ = '산화수소'  # S
    crop_name_ = '스치'
    grade_ = get_grade(crop_name_)
    print(get_crop_duration(crop_name_), get_grade_name(grade_), get_grade_duration(grade_), sep='\t')
