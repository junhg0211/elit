from discord import User
from discord.ext.commands import Cog, Bot, group, Context, has_role, CommandError, MissingRole, command

from elit import get_player, get_item_name_by_type
from util import const


class InventoryCommand(Cog):
    @group(aliases=['인벤토리', '인벤'],
           description='자신의 인벤토리를 확인합니다.',
           invoke_without_command=True)
    async def inventory(self, ctx: Context):
        player = get_player(ctx.author.id)
        await ctx.send(str(player.get_inventory()))

    @has_role(const('role.enifia'))
    @command(aliases=['주기'],
             description='아이템을 줍니다.')
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
