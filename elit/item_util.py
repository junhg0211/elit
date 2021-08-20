from math import inf

import elit.item


def get_item_classes():
    __dir = dir(elit.item)
    for variable in __dir:
        if not variable.startswith('__') and variable[0].upper() == variable[0]:
            item_class = eval(f'elit.item.{variable}')
            if issubclass(item_class, elit.item.Item):
                yield item_class


def get_item_class_by_type(item_type: int):
    for item_class in get_item_classes():
        if item_class.type == item_type:
            return item_class


def get_item_object(item_type, amount, item_id) -> elit.item.Item:
    return get_item_class_by_type(item_type)(amount, item_id)


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
