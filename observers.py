import threading
import time
import asyncio
import requests

import config
from instance_actions import InstanceState
import discord

settings = config.SettingsConfig()

class GeneralState:
    stopped = 0
    starting = 1
    running = 2
    stopping = 3
    invalid = 4

instance_state_map = {
    InstanceState.pending: GeneralState.starting,
    InstanceState.running: GeneralState.running,
    InstanceState.shutting_down: GeneralState.invalid,
    InstanceState.terminated: GeneralState.invalid,
    InstanceState.stopping: GeneralState.stopping,
    InstanceState.stopped: GeneralState.stopped
}

macaw_state_map = {
    'starting': GeneralState.starting,
    'running': GeneralState.running,
    'stopping': GeneralState.stopping,
    'stopped': GeneralState.stopped
}

STATE_EMOJIS = ['red_square', 'orange_square', 'green_square', 'white_large_square', 'warning']
STATE_DISPLAY_NAMES = ['Stopped', 'Starting', 'Running', 'Stopping', 'Invalid State']

class StartObserver:
    def __init__(self, manager, message):
        self._manager = manager
        self._message = message

    async def _setEmbed(self, instance_state: int, macaw_state: int, mc_state: int):
        if instance_state == GeneralState.stopped and macaw_state == GeneralState.stopped and mc_state == GeneralState.stopped:
            colour = 0xd11f00
        elif instance_state == GeneralState.running and macaw_state == GeneralState.running and mc_state == GeneralState.running:
            colour = 0x04d45b
        else:
            colour = 0xb8b9ba

        embed = discord.Embed(title='Starting...', color=colour)
        embed.add_field(name='EC2 Instance', value=':{}: {}'.format(STATE_EMOJIS[instance_state], STATE_DISPLAY_NAMES[instance_state]))

        await self._message.edit(embed=embed) 

    async def _waitForInstance(self):
        prev_state = None
        state = self._manager.get_state()

        await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

        while state != InstanceState.running:
            time.sleep(settings.check_delay)

            if state != prev_state:
                await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

            prev_state = state
            state = self._manager.get_state()
        
        await self._setEmbed(instance_state_map[state], GeneralState.stopped, GeneralState.stopped)

    async def _waitForMacaw(self):
        prev_state = None
        state = GeneralState.stopped

        while state != GeneralState.running:

            time.sleep(settings.check_delay)

    async def _run(self):
        await self._waitForInstance()
        # await self._waitForMacaw()

    async def dispatch(self):
        await self._run()