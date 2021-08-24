from math import inf
from typing import Optional, Type

import elit.item
from util import database

duplication_prohibited = (elit.item.Crop.type,)


def get_item_classes():
    __dir = dir(elit.item)
    for variable in __dir:
        if not variable.startswith('__') and variable[0].upper() == variable[0]:
            item_class = eval(f'elit.item.{variable}')
            if issubclass(item_class, elit.item.Item):
                yield item_class


def get_item_class_by_type(item_type: int) -> Optional[Type[elit.item.Item]]:
    """
    타입 번호가 ``item_type`` 인 아이템의 클래스를 출력합니다.
    만약 결과에 해당되는 클래스가 없는 경우에는 ``None`` 을 반환합니다.
    """
    for item_class in get_item_classes():
        if item_class.type == item_type:
            return item_class


def get_item_object(item_type, item_id) -> elit.item.Item:
    return get_item_class_by_type(item_type)(item_id)


def get_item_type(item_id) -> Optional[int]:
    with database.cursor() as cursor:
        cursor.execute('SELECT item_type FROM inventory WHERE item_id = %s', item_id)
        data = cursor.fetchall()
    if data:
        return data[0][0]


def get_item_object_by_id(item_id: int) -> Optional[elit.item.Item]:
    item_type = get_item_type(item_id)
    if item_type is None:
        return
    return get_item_object(item_type, item_id)


def get_item_name_by_type(item_type: int) -> str:
    item_class = get_item_class_by_type(item_type)
    if item_class is None:
        return ''
    else:
        return item_class.name


def get_max_type_number() -> int:
    max_ = -inf
    for item_class in get_item_classes():
        max_ = max(max_, item_class.type)
    return max_


if __name__ == '__main__':
    print(*get_item_classes())
    print(get_item_class_by_type(0))
    print(get_item_name_by_type(0))
    print(get_max_type_number())
