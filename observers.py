import time

import discord

import config
from instance_actions import InstanceState
from macaw_actions import MacawState

settings = config.SettingsConfig()


class GeneralState:
    stopped = 0
    starting = 1
    running = 2
    stopping = 3
    invalid = 4


# Map for instance states to general states.
instance_state_map = {
    InstanceState.pending: GeneralState.starting,
    InstanceState.running: GeneralState.running,
    InstanceState.shutting_down: GeneralState.invalid,
    InstanceState.terminated: GeneralState.invalid,
    InstanceState.stopping: GeneralState.stopping,
    InstanceState.stopped: GeneralState.stopped
}

# Map for Macaw states to general states.
macaw_state_map = {
    MacawState.starting: GeneralState.starting,
    MacawState.running: GeneralState.running,
    MacawState.stopping: GeneralState.stopping,
    MacawState.stopped: GeneralState.stopped,
    MacawState.instance_stopped: GeneralState.stopped,
    MacawState.macaw_starting: GeneralState.starting
}

# The emojis that get displayed in the embed for each of general states.
STATE_EMOJIS = ['red_square', 'orange_square', 'green_square', 'white_large_square', 'warning']

# The names for the states that will be used in the embeds.
STATE_DISPLAY_NAMES = ['Stopped', 'Starting', 'Running', 'Stopping', 'Invalid State']


#
# Observe the server starting up and edit an embed accordingly.
# This class will block the bot from accepting commands until all servers have started.
#
class StartObserver:
    def __init__(self, aws_manager, macaw_manager, message):
        self._aws_manager = aws_manager
        self._macaw_manager = macaw_manager
        self._message = message

    # Edits the message in self._message to a new embed, constructed using the
    # states of the various servers.
    async def _setEmbed(self, instance_state: int, macaw_state: int, mc_state: int):
        if instance_state == GeneralState.stopped and \
                macaw_state == GeneralState.stopped and \
                mc_state == GeneralState.stopped:
            # All processes are stopped, red embed.
            colour = 0xd11f00
        elif instance_state == GeneralState.running and \
                macaw_state == GeneralState.running and \
                mc_state == GeneralState.running:
            # All processes are running, green embed.
            colour = 0x04d45b
        else:
            # Processes are starting, grey embed.
            colour = 0xb8b9ba

        # Construct the embed.
        embed = discord.Embed(title='Starting...', color=colour)
        embed.add_field(name='EC2 Instance', value=':{}: {}'.format(STATE_EMOJIS[instance_state], STATE_DISPLAY_NAMES[instance_state]))
        embed.add_field(name='Macaw Server', value=':{}: {}'.format(STATE_EMOJIS[macaw_state], STATE_DISPLAY_NAMES[macaw_state]))
        embed.add_field(name='Minecraft Server', value=':{}: {}'.format(STATE_EMOJIS[mc_state], STATE_DISPLAY_NAMES[mc_state]))

        # Update the message with the new embed.
        await self._message.edit(embed=embed) 

    # Blocks until the instance is in the 'running' state.
    # Updates the embed when the instance state changes.
    async def _wait_for_instance(self):
        prev_state = None
        state = self._aws_manager.get_state()

        await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

        while state != InstanceState.running:
            time.sleep(settings.check_delay)

            if state != prev_state:
                await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

            prev_state = state
            state = self._aws_manager.get_state()
        
        await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

    # Blocks until the Minecraft and Macaw servers are in the 'running' state.
    # Updates the embed when the server state changes.
    async def _wait_for_macaw(self):
        prev_state = None
        state = self._macaw_manager.get_state()

        while state != MacawState.running:
            if state != prev_state:
                if state == MacawState.macaw_starting:
                    await self._setEmbed(GeneralState.running, macaw_state_map[state], GeneralState.stopped)
                else:
                    await self._setEmbed(GeneralState.running, GeneralState.running, macaw_state_map[state])

            time.sleep(settings.check_delay)

            prev_state = state
            state = self._macaw_manager.get_state()

        if state == MacawState.macaw_starting:
            await self._setEmbed(GeneralState.running, macaw_state_map[state], GeneralState.stopped)
        else:
            await self._setEmbed(GeneralState.running, GeneralState.running, macaw_state_map[state])

    # Start observing server states.
    async def dispatch(self):
        await self._wait_for_instance()
        await self._wait_for_macaw()
