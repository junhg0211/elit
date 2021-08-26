from typing import Tuple, Optional

from discord import Embed
from discord.ext.commands import Bot, Context

from elit import get_prise
from elit.item import Item
from util import eul_reul, const, eun_neun


class Crop(Item):
    type = 4
    name = '작물'
    description = '밭에서 수확하고 얻은 작물입니다.'

    def __init__(self, item_id: int):
        super().__init__(item_id)

        self.name = self.get_name()
        self.quality = self.get_quality()

    def __str__(self):
        return f'`{self.item_data.id}`: 작물-{self.name}'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.amount += 1
        return f'엥...? `{self.name}`{eul_reul(self.name)} 사용하고 다시 얻었다! ' \
               f'`{self.name}`{eun_neun(self.name)} <#{const("text_channel.shop")}>에서 판매하자!', None

    def get_prise_per_piece(self) -> int:
        return get_prise(self.name)

    def set_name(self, name: str) -> 'Crop':
        self.name = name
        self.item_data.set_data('crop_name', name)
        return self

    def set_quality(self, quality: float) -> 'Crop':
        self.quality = quality
        self.item_data.set_data('quality', quality)
        return self

    def get_name(self) -> str:
        return self.item_data.get_data('crop_name')

    def get_quality(self) -> float:
        raw_quality = self.item_data.get_data('quality')
        if raw_quality is None:
            return 0.0
        else:
            return raw_quality
