from asyncio import TimeoutError as AsyncioTimeoutError
from typing import Tuple

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.exception import ChannelError
from elit.item import Item
from util import byte_len, message_author_check


class Seed(Item):
    name = '씨앗'
    type = 3
    description = '밭에 농작물을 심을 수 있습니다.'

    async def use(self, amount: int, player, bot: Bot, ctx: Context) -> Tuple[str, Embed]:
        self.check_amount(amount)

        farm = player.get_farm()
        farm_channel = farm.get_channel(bot)

        if ctx.channel != farm_channel:
            raise ChannelError(f':x: {ctx.author.mention} **여기서는 농작물을 심을 수 없어요!** '
                               f'{farm_channel.mention}에서 시도해주세요.')

        await ctx.send(f':potted_plant: 심을 농작물의 이름을 입력해주세요. 농작물은 __{amount}개__를 심습니다. '
                       f'(`취소` 또는 `cancel`이라고 입력하면 심기가 취소됩니다.)')
        try:
            message = await bot.wait_for('message', check=message_author_check(ctx.author), timeout=15)
        except AsyncioTimeoutError:
            raise AsyncioTimeoutError(f':x: {ctx.author.mention} **작물 심기가 취소되었습니다.** '
                                      f'작물 이름 입력 시간이 초과되었어요...')
        else:
            if message.content in ('취소', 'cancel'):
                raise ValueError(':x: **심기를 취소했습니다.**')
            crop_name = message.content

        if byte_len(crop_name) > 16:
            raise ValueError(f':x: {ctx.author.mention} **작물 이름이 너무 길어요!** '
                             f'작물 이름은 16바이트(한글 8글자, 영문 16글자) 이내로 지어주세요!')

        amount, planted_at = farm.plant(crop_name, amount)

        embed = farm.get_planted_crop_by_name(crop_name).get_embed()
        return self.apply_use(amount, f':potted_plant: {farm_channel.mention}에 '
                                      f'`{crop_name}` __{amount}개__를 심었습니다.'), embed
