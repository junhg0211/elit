from json import load

with open('res/const.json', 'r', encoding='utf-8') as file:
    _const = load(file)

with open('res/secret.json', 'r') as file:
    _secret = load(file)


def get_json_value_by_path(dictionary: dict, path: str):
    tokens = path.split('.')
    result = dictionary
    while tokens:
        if tokens[0]:
            result = result[tokens.pop(0)]
        else:
            break
    return result


def const(path: str):
    return get_json_value_by_path(_const, path)


def secret(path: str):
    return get_json_value_by_path(_secret, path)
