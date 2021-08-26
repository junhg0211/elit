from datetime import timedelta, datetime
from hashlib import md5
from math import exp
from random import seed, random
from typing import Tuple

from discord import Embed

from util import linear, cubic, const


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


if __name__ == '__main__':
    # crop_name_ = '산화수소'  # S
    crop_name_ = '스치'
    grade_ = get_grade(crop_name_)
    print(get_crop_duration(crop_name_), get_grade_name(grade_), get_grade_duration(grade_), sep='\t')
