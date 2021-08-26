# noinspection SpellCheckingInspection
def a_ya(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '아' if (ord(string) - 44032) % 28 else '야'
    elif string in '1234567890':
        return '아' if string in '136780' else '야'
    else:
        return '아' if string not in 'aeiouyw' else '야'


# noinspection SpellCheckingInspection
def eul_reul(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '을' if (ord(string) - 44032) % 28 else '를'
    elif string in '1234567890':
        return '을' if string in '136780' else '를'
    else:
        return '을' if string not in 'aeiouyw' else '를'


# noinspection SpellCheckingInspection
def eun_neun(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '은' if (ord(string) - 44032) % 28 else '는'
    elif string in '1234567890':
        return '은' if string in '136780' else '는'
    else:
        return '은' if string not in 'aeiouyw' else '는'


# noinspection SpellCheckingInspection
def i_ga(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '이' if (ord(string) - 44032) % 28 else '가'
    elif string in '1234567890':
        return '이' if string in '136780' else '가'
    else:
        return '이' if string not in 'aeiouyw' else '가'


# noinspection SpellCheckingInspection
def euro(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '와' if (ord(string) - 44032) % 28 in [0, 8] else '으로'
    elif string in '1234567890':
        return '으로' if string in '360' else '로'
    else:
        return '으로' if string not in 'aeiouyw' else '로'


# noinspection SpellCheckingInspection
def ina(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '나' if (ord(string) - 44032) % 28 in [0, 8] else '이나'
    elif string in '1234567890':
        return '이나' if string in '360' else '나'
    else:
        return '이나' if string not in 'aeiouyw' else '나'


# noinspection SpellCheckingInspection
def irago(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '라고' if (ord(string) - 44032) % 28 in [0, 8] else '이라고'
    elif string in '1234567890':
        return '이라고' if string in '360' else '라고'
    else:
        return '이라고' if string not in 'aeiouyw' else '라고'


# noinspection SpellCheckingInspection
def wa_gwa(string: str):
    string = string[-1]

    if 44032 <= ord(string):
        return '라고' if (ord(string) - 44032) % 28 in [0, 8] else '과'
    elif string in '1234567890':
        return '과' if string in '360' else '와'
    else:
        return '과' if string not in 'aeiouyw' else '와'
