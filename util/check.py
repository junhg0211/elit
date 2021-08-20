from discord import Reaction, User, Message, Emoji


def emoji_reaction_check(message: Message, emoji: Emoji, user: User):
    def _check(reaction: Reaction, reaction_user: User):
        return reaction.message == message \
               and reaction_user == user \
               and reaction.emoji == emoji
    return _check


def message_author_check(user: User):
    def _check(message: Message):
        return message.author == user
    return _check
