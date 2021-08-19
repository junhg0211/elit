from discord import User, Embed
from discord.ext.commands import Cog, Bot, group, Context, has_role, CommandError, MissingRole, command

from elit import get_player, get_item_name_by_type, get_max_type_number
from util import const


class InventoryCommand(Cog):
    @group(name='인벤토리', aliases=['인벤'], description='자신의 인벤토리를 확인합니다.', invoke_without_command=True)
    async def inventory(self, ctx: Context):
        player = get_player(ctx.author.id)
        inventory = player.get_inventory()
        embed = Embed(title='인벤토리', description=ctx.author.display_name, color=const('color.elit'))
        inventory_capacity = inventory.get_capacity()
        embed.add_field(name='용량', value=f'{inventory_capacity}/{inventory.size} '
                                         f'({inventory_capacity / inventory.size * 100:.2f}%)', inline=False)
        embed.add_field(name='구성품', value=str(inventory))
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @command(name='타입', aliases=['type'], description='아이템 타입 목록을 확인합니다.')
    async def type(self, ctx: Context):
        types = list()
        for type_number in range(get_max_type_number() + 1):
            if (name := get_item_name_by_type(type_number)) is not None:
                types.append(f'{type_number}: {name}')

        embed = Embed(title='사용 가능한 아이템 타입 목록', color=const('color.elit'),
                      description='\n'.join(types))
        await ctx.send(embed=embed)

    @has_role(const('role.enifia'))
    @command(name='주기', aliases=['give'], description='아이템을 줍니다.', hidden=True)
    async def give(self, ctx: Context, user: User, item_type: int, amount: int = 1):
        get_player(user.id).get_inventory().add_item(item_type, amount)
        await ctx.send(f':baggage_claim: __{user.display_name}__님에게 '
                       f'__{get_item_name_by_type(item_type)}__ __{amount}개__를 주었습니다!')

    @give.error
    async def give_error(self, ctx: Context, error: CommandError):
        if isinstance(error, MissingRole):
            role = ctx.guild.get_role(const('role.enifia'))
            await ctx.send(f':baggage_claim: 이 커맨드를 사용하려면 __{role.name}__ 역할이 있어야 돼요!')


def setup(bot: Bot):
    bot.add_cog(InventoryCommand())
