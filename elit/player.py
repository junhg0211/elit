from asyncio import wait
from typing import List

from discord import User
from discord.ext.commands import Bot
from pymysql.cursors import DictCursor

from elit import get_item_object, Farm, Item
from elit.exception import CapacityError, InventoryCapacityError
from util import database


def next_item_id():
    with database.cursor() as cursor:
        cursor.execute('SELECT AUTO_INCREMENT '
                       'FROM information_schema.TABLES '
                       'WHERE TABLE_SCHEMA = "elit" AND TABLE_NAME = "inventory"')
        return cursor.fetchall()[0][0]


class PlayerInventory:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id
        self.items: List[Item] = list()

        with database.cursor() as cursor:
            cursor.execute('SELECT inventory_size FROM player WHERE discord_id = %s', self.discord_id)
            self.size = cursor.fetchall()[0][0]

        self.load_items()

    def __str__(self):
        return str(self.items)

    def is_item(self, item_type: int) -> bool:
        for item in self.items:
            if item.type == item_type:
                return True
        return False

    def get_item(self, item_type: int) -> Item:
        for item in self.items:
            if item.type == item_type:
                return item

    def get_capacity(self):
        """아이템 가지고 있는 개수"""
        result = 0
        for item in self.items:
            result += item.amount
        return result

    def get_free_space(self) -> bool:
        """더 담을 수 있는 아이템 개수"""
        return self.size - self.get_capacity()

    def add_item(self, item_type: int, amount: int = 1) -> 'PlayerInventory':
        """
        인벤토리에 아이템을 담습니다.

        :exception InventoryCapacityError: 더 이상 인벤토리에 아이템을 담을 수 없음
        """

        amount = min(amount, self.get_free_space())

        if amount <= 0:
            raise InventoryCapacityError('이 인벤토리에 더 이상 아이템을 담을 수 없습니다.')

        item = self.get_item(item_type)
        if item is not None:
            item.set_amount(item.amount + amount)
            return self

        with database.cursor() as cursor:
            cursor.execute('INSERT INTO inventory(discord_id, item_type, amount) '
                           'VALUES (%s, %s, %s)', (self.discord_id, item_type, amount))
        return self.load_items()

    def load_items(self) -> 'PlayerInventory':
        with database.cursor() as cursor:
            cursor.execute('SELECT item_type, amount, item_id FROM inventory WHERE discord_id = %s', self.discord_id)
            items = cursor.fetchall()
        self.items = list()
        for item_type, amount, item_id in items:
            item = get_item_object(item_type, amount, item_id)
            if item is not None:
                self.items.append(item)
        return self


class Player:
    def __init__(self, discord_id: int):
        """
        게임 플레이어로써의 유저 객체입니다.
        아이디를 입력하면 데이터베이스에서 자동으로 해당 아이디에 해당하는 플레이어 정보를 fetch하여 객체를 생성합니다.

        :param discord_id: 유저 객체의 아이디.
        :exception ValueError: `discord_id`에 해당하는 플레이어가 데이터베이스에 존재하지 않을 때 발생합니다.
        """

        self.discord_id = discord_id

        with database.cursor(DictCursor) as cursor:
            cursor.execute('SELECT farm_id, money FROM player WHERE discord_id = %s', self.discord_id)
            data = cursor.fetchall()
        if not data:
            raise ValueError('해당 ID를 가진 플레이어에 대한 정보가 존재하지 않습니다.')
        else:
            data = data[0]

        self.farm_id = data['farm_id']
        self.money = data['money']

    def get_inventory(self) -> PlayerInventory:
        return PlayerInventory(self.discord_id)

    def set_money(self, amount: int) -> 'Player':
        self.money = amount
        with database.cursor() as cursor:
            cursor.execute('UPDATE player SET money = %s WHERE discord_id = %s', (amount, self.discord_id))
        return self

    def get_user(self, bot: Bot) -> User:
        return bot.get_user(self.discord_id)

    def get_farm(self) -> Farm:
        return Farm(self.farm_id)

    def is_in_farm(self):
        return self.farm_id is not None

    def is_farm(self, channel_id: int) -> bool:
        return self.farm_id == channel_id

    async def leave_farm(self, bot: Bot) -> 'Player':
        farm = Farm(self.farm_id)
        farm_channel = farm.get_channel(bot)

        self.farm_id = None
        with database.cursor() as cursor:
            cursor.execute('UPDATE player SET farm_id = NULL WHERE discord_id = %s', self.discord_id)

        user = self.get_user(bot)
        await wait((
            farm.check_empty(bot),
            farm_channel.send(f':people_wrestling: {user.mention}님이 밭을 떠났습니다!')))
        return self

    async def join(self, farm: Farm, bot: Bot):
        farm_channel = farm.get_channel(bot)
        with database.cursor() as cursor:
            cursor.execute('UPDATE player SET farm_id = %s WHERE discord_id = %s', (farm.id, self.discord_id))

        if farm.capacity <= farm.member_count():
            raise CapacityError(f'이 밭(id: {farm.id})은 {farm.capacity}명 초과로 구성원을 받을 수 없습니다.')

        user = self.get_user(bot)
        await farm_channel.send(f':people_wrestling: 새로운 구성원 {user.mention}님을 반겨주세요!')


def new_player(discord_id: int) -> Player:
    with database.cursor() as cursor:
        cursor.execute('INSERT INTO player(discord_id, money) VALUES (%s, 0)', discord_id)
    return Player(discord_id)


def get_player(discord_id: int) -> Player:
    try:
        return Player(discord_id)
    except ValueError:
        return new_player(discord_id)


def get_money_leaderboard(limit: int, from_: int = 0) -> tuple:
    """
    ``discord_id``, ``money``가 담겨있는 raw data가 다음과 같은 형태로 주어집니다.
    ``({'discord_id': ..., 'money': ...}, {'discord_id': ..., 'money': ...})``

    :param limit: 정보의 개수
    :param from_: 처음 정보 번째수
    :return:
    """
    with database.cursor(DictCursor) as cursor:
        cursor.execute('SELECT discord_id, money FROM player ORDER BY money DESC LIMIT %s, %s', (from_, limit))
        return cursor.fetchall()[from_:from_ + limit]
