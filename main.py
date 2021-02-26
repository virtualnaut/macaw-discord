import re

import discord

import config
import observers
from permissions import allowed_commands, can_run, Action
from aws_actions import AWSManager
from macaw_actions import MacawManager

credentials = config.CredentialsConfig()
aws_config = config.AWSConfig()
settings = config.SettingsConfig()

aws = AWSManager()
macaw = MacawManager(aws)

STATUS_COLOURS = {
    0: 0xb8b9ba,
    16: 0x04d45b,
    32: 0xa6003a,
    48: 0x57001e,
    64: 0xd18100,
    80: 0xd11f00
}

class EmbedColours:
    FAIL = 0xd11f00
    SUCCESS = 0x04d45b


class MacawBot(discord.Client):
    def __init__(self):
        super().__init__()

        self._commands = {
            'help': (self._cmd_help, '`>help`: Display this help message.'),
            'start': (self._cmd_start, '`>start`: Start the servers and instance.'),
            'stop': (self._cmd_stop, '`>stop`: Stop the servers and instance.'),
            'status': (self._cmd_status, '`>status`: Get the current status of the instance.'),
            'issue': (self._cmd_issue, '`>issue [COMMAND]`: Issue a command to the Minecraft server.'),
            'players': (self._cmd_players, '`>players`: Get a list of currently online players.'),
            'dynmap': (self._cmd_dynmap, '`>dynmap`: Get the current dynmap address.')
        }

    async def on_ready(self):
        print('Bot started.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not message.content.startswith('>'):
            return

        commands = self._commands.values()
        for command, _ in commands:
            if can_run(command, message.author, message.guild):
                await command(message)

    async def _cmd_start(self, message):
        if message.content == '>start':
            result = aws.start()
            
            if result[0]:
                embed = discord.Embed(title='Starting...', color=0xd11f00, description='No public IP address yet...')
                embed.add_field(name='EC2 Instance', value=':red_square: Stopped')
                embed.add_field(name='Macaw Server', value=':red_square: Stopped')
                embed.add_field(name='Minecraft Server', value=':red_square: Stopped')

                message = await message.channel.send(embed=embed)

                observer = observers.StartObserver(aws, macaw, message)
                await observer.dispatch()
            else:
                embed = discord.Embed(title='Cannot Start Instance!', color=0xd11f00, description=result[1])
                await message.channel.send(embed=embed)

    async def _cmd_stop(self, message):
        if message.content == '>stop':
            # result = aws.stop()
            result = macaw.shutdown()
            
            if result[0]:
                embed = discord.Embed(title='Stopping...', color=0xd11f00)
                embed.add_field(name='EC2 Instance', value=':green_square: Running')
                embed.add_field(name='Macaw Server', value=':green_square: Running')
                embed.add_field(name='Minecraft Server', value=':green_square: Running')

                message = await message.channel.send(embed=embed)

                observer = observers.StopObserver(aws, macaw, message)
                await observer.dispatch()
            else:
                embed = discord.Embed(title='Cannot Stop Instance!', color=0xd11f00, description=result[1])
                await message.channel.send(embed=embed)

    async def _cmd_status(self, message):
        if message.content == '>status':
            status = aws.get_status()
            embed = discord.Embed(
                title='Instance Status',
                color=STATUS_COLOURS[status['state_code']]
            )
            embed.add_field(name='Instance ID', value=status['instance_id'], inline=False)
            embed.add_field(name='Status', value=status['state_name'].title(), inline=False)

            if status['state_reason'] != '':
                embed.add_field(name='Reason', value=status['state_reason'], inline=False)

            if status['ip_address'] is not None:
                embed.add_field(name='Public IP Address', value=status['ip_address'], inline=False)

            await message.channel.send(embed=embed)

    async def _cmd_issue(self, message):
        if message.content.startswith('>issue'):
            result = macaw.issue(message.content[7:])

            if result[0]:
                embed = discord.Embed(title='Success', color=EmbedColours.SUCCESS, description=result[1])
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Command not issued', color=EmbedColours.FAIL, description=result[1])
                await message.channel.send(embed=embed)

    async def _cmd_players(self, message):
        if message.content == '>players':
            result = macaw.get_online_players()

            if result[0]:
                embed = discord.Embed(title='Online Players', color=EmbedColours.SUCCESS, description=result[1])
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Cannot get players', color=EmbedColours.FAIL, description=result[1])
                await message.channel.send(embed=embed)

    async def _cmd_dynmap(self, message):
        if message.content == '>dynmap':
            ip_address = aws.get_public_ip()

            if ip_address is not None:
                embed = discord.Embed(title='Dynmap', color=EmbedColours.SUCCESS, description='{}:{}'.format(ip_address, settings.dynmap_port))
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Failed', color=EmbedColours.FAIL, description='Can\'t get the dynmap address if the instance isn\'t running!')
                await message.channel.send(embed=embed)

    async def _cmd_help(self, message):
        if message.content == '>help':
            commands = allowed_commands(message.author, message.guild)
            content = 'You don\'t have permission to use any commands'
            
            if len(commands) != 0:
                lines = []
                for command in commands:
                    lines.append(self._commands[command][1])
                content = '\n'.join(lines)

            embed = discord.Embed(title='Commands', color=EmbedColours.SUCCESS, description=content)
            await message.channel.send(embed=embed)


client = MacawBot()
client.run(credentials.discord_bot_token)