from typing import Tuple

from discord import Embed
from discord.ext.commands import Bot, Context

from elit.exception import ChannelError
from elit.item import Item
from util import byte_len, const


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

        await ctx.send(':potted_plant: 심을 농작물의 이름을 입력해주세요.')
        message = await bot.wait_for('message', timeout=30)
        # except: raise f':x: {ctx.author.mention} **작물 심기가 취소되었습니다.** 작물 이름 입력 시간이 초과되었어요...'
        crop_name = message.content

        if byte_len(crop_name) > 16:
            raise ValueError(f':x: {ctx.author.mention} **작물 이름이 너무 길어요!** '
                             f'작물 이름은 16바이트(한글 8글자, 영문 16글자) 이내로 지어주세요!')

        amount, planted_at = farm.plant(crop_name, amount)

        embed = Embed(title='작물 심음', color=const('color.elit'))
        embed.add_field(name='이름', value=crop_name)
        embed.add_field(name='심은 개수', value=amount)
        embed.add_field(name='심은 날짜', value=str(planted_at))

        return self.apply_use(amount, f':potted_plant: {farm_channel.mention}에 `{crop_name}` {amount}개를 심었습니다.'), embed
