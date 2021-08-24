from typing import Tuple, Optional

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.item import Item


class Testimonial(Item):
    name = '상장'
    type = 8
    description = '여러가지 칭찬할만 한 일을 했을 때 받을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        self.amount += 1
        return '서버 추천인을 입력하거나 출석을 하면 상장을 받을 수 있다! **상장은 `엘 교환상점`에서 좋은 아이템으로 교환할 수 있다.**', None

    async def get_prise_per_piece(self) -> int:
        return 100
