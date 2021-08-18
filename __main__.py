from os import listdir

from discord.ext.commands import Bot

from util import const, i_ga, secret

bot = Bot(const('command_prefix'))

for file_name in listdir('cogs'):
    if file_name.endswith('.py'):
        bot.load_extension(f'cogs.{file_name[:-3]}')
        print(f'{file_name}{i_ga(file_name)} 준비되었습니다.')

bot.run(secret('bot_token'))
