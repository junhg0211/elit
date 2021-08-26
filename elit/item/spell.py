from typing import Tuple, Optional

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.item import Item
from util import eul_reul


class InventorySizeSpell(Item):
    quantity = 100

    type = 9
    name = f'{quantity}칸 인벤토리 확장 주문서'
    description = '가질 수 있는 아이템의 양을 100만큼 늘릴 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Optional[Embed]]:
        player_inventory = player.get_inventory()
        player_inventory.set_size(player_inventory.size + self.quantity)
        return f':baggage_claim: `{self.name}`{eul_reul(self.name)} 사용해서 인벤토리 크기를 ' \
               f'__{player_inventory.size}칸__으로 늘렸다!', None

    async def get_prise_per_piece(self) -> int:
        return 2000
