from discord.ext.commands import Cog, Bot, command, Context

from util import const


def check_farm(ctx: Context, bot: Bot):
    shop_channel = bot.get_channel(const('text_channel.shop'))
    if ctx.channel != shop_channel:
        return f':shopping_cart: {ctx.author.mention} **이 명령어를 사용하기 위해서는 {shop_channel.mention}에 있어야 해요!**'
    return False


class Shop(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name='상점', aliases=['shop'], description='상점으로 이동합니다.')
    async def shop(self, ctx: Context):
        shop_channel = self.bot.get_channel(const('text_channel.shop'))

        if ctx.channel == shop_channel:
            await ctx.send(f':shopping_cart: 여기는 {shop_channel.mention}입니다!')
        else:
            await ctx.send(f':shopping_cart: {shop_channel.mention}에 가려면 이곳을 눌러주세요: {shop_channel.mention}')


def setup(bot: Bot):
    bot.add_cog(Shop(bot))
