import config

settings = config.SettingsConfig()


class Action:
    STOP = 0
    START = 1
    STATUS = 2
    ISSUE = 3
    VIEW_PLAYERS = 4
    DYNMAP = 5


permissions = {
    'starter': [Action.START],
    'stopper': [Action.STOP],
    'status': [Action.STATUS],
    'admin': [
        Action.START,
        Action.STOP,
        Action.STATUS,
        Action.ISSUE,
        Action.VIEW_PLAYERS,
        Action.DYNMAP
    ],
    'trusted': [
        Action.START,
        Action.STATUS,
        Action.VIEW_PLAYERS,
        Action.DYNMAP
    ]
}

command_requirements = {
    'help': [],
    'start': [Action.START],
    'stop': [Action.STOP],
    'status': [Action.STATUS],
    'issue': [Action.ISSUE],
    'players': [Action.VIEW_PLAYERS],
    'dynmap': [Action.DYNMAP]
}

def get_actions(member, guild):
    roles = settings.roles.items()
    member_actions = set()

    for (role_identifier, role_name) in roles:

        match = list(filter(lambda i: i.name == role_name, guild.roles))

        if len(match) == 0:
            continue

        role = match[0]

        if role in member.roles:
            member_actions = member_actions.union(set(permissions[role_identifier]))

    return member_actions

def can_perform(action, member, guild):
    if member.id == settings.owner:
        return True

    if action in get_actions(member, guild):
        return True

    return False

def can_run(command, member, guild):
    if member.id == settings.owner:
        return True
        
    member_actions = get_actions(member, guild)

    if len(set(command_requirements[command]).difference(member_actions)) == 0:
        return True

    return False

def allowed_commands(member, guild):
    if member.id == settings.owner:
        return command_requirements.keys()

    permitted = []
    member_actions = get_actions(member, guild)

    requirements_items = command_requirements.items()
    for command, requirements in requirements_items:
        if len(set(requirements).difference(member_actions)) == 0:
            permitted.append(command)

    return permitted