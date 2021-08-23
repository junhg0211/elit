from typing import Tuple, Optional

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.item import Item


class RecommendationCertificate(Item):
    name = '추천 증명서'
    type = 8
    description = '다른 사람에게 엘리트를 추천했다는 증명서!'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.amount += 1
        return '추천을 하면 추천서를 받을 수 있다! **추천서는 교환상점에서 좋은 아이템으로 교환할 수 있다.**', None

    async def get_prise_per_piece(self) -> int:
        return 10000
