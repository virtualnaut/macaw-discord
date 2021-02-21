import config

settings = config.SettingsConfig()


class Action:
    STOP = 0
    START = 1
    STATUS = 2
    USAGE = 3


permissions = {
    'starter': [Action.START],
    'stopper': [Action.STOP],
    'status': [Action.STATUS],
    'admin': [Action.START, Action.STOP, Action.STATUS, Action.USAGE],
    'trusted': [Action.START, Action.STATUS, Action.USAGE]
}


def can_perform(action, member, guild):
    if member.id == settings.owner:
        return True

    roles = settings.roles.items()

    member_actions = set()

    for (role_identifier, role_name) in roles:

        match = list(filter(lambda i: i.name == role_name, guild.roles))

        if len(match) == 0:
            continue

        role = match[0]

        if role in member.roles:
            member_actions = member_actions.union(set(permissions[role_identifier]))

    if action in member_actions:
        return True

    return False


