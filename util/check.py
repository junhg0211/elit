from discord import Reaction, User


def emoji_reaction_check(message, emoji, user):
    def check_(reaction: Reaction, reaction_user: User):
        return reaction.message == message \
               and reaction_user == user \
               and reaction.emoji == emoji
    return check_
