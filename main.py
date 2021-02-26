import re

import discord

import config
import observers
from permissions import can_perform, Action
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
    async def on_ready(self):
        print('Bot started.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not message.content.startswith('>'):
            return

        if (message.content == '>start') and (can_perform(Action.START, message.author, message.guild)):
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

        elif (message.content == '>stop') and (can_perform(Action.STOP, message.author, message.guild)):
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

        elif (message.content == '>status') and (can_perform(Action.STATUS, message.author, message.guild)):
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

        elif (message.content.startswith('>issue')) and (can_perform(Action.ISSUE, message.author, message.guild)):
            result = macaw.issue(message.content[7:])

            if result[0]:
                embed = discord.Embed(title='Success', color=EmbedColours.SUCCESS, description=result[1])
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Command not issued', color=EmbedColours.FAIL, description=result[1])
                await message.channel.send(embed=embed)

        elif (message.content == '>players') and (can_perform(Action.VIEW_PLAYERS, message.author, message.guild)):
            result = macaw.get_online_players()

            if result[0]:
                embed = discord.Embed(title='Online Players', color=EmbedColours.SUCCESS, description=result[1])
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Cannot get players', color=EmbedColours.FAIL, description=result[1])
                await message.channel.send(embed=embed)

        elif (message.content == '>dynmap') and (can_perform(Action.DYNMAP, message.author, message.guild)):
            ip_address = aws.get_public_ip()

            if ip_address is not None:
                embed = discord.Embed(title='Dynmap', color=EmbedColours.SUCCESS, description='{}:{}'.format(ip_address, settings.dynmap_port))
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title='Failed', color=EmbedColours.FAIL, description='Can\'t get the dynmap address if the instance isn\'t running!')
                await message.channel.send(embed=embed)


client = MacawBot()
client.run(credentials.discord_bot_token)