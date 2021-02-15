import discord
import config
from instance_actions import AWSManager

credentials = config.CredentialsConfig()
aws_config = config.AWSConfig()

aws = AWSManager()

STATUS_COLOURS = {
    0: 0xb8b9ba,
    16: 0x04d45b,
    32: 0xa6003a,
    48: 0x57001e,
    64: 0xd18100,
    80: 0xd11f00
}


class MacawBot(discord.Client):
    async def on_ready(self):
        print('Bot started.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content == '>start':
            result = aws.start()
            
            if result[0]:
                await message.channel.send('Starting instance...')
            else:
                embed = discord.Embed(title='Cannot Start Instance!', color=0xd11f00, description=result[1])
                await message.channel.send(embed=embed)

        elif message.content == '>stop':
            result = aws.stop()
            
            if result[0]:
                await message.channel.send('Stopping instance...')
            else:
                embed = discord.Embed(title='Cannot Stop Instance!', color=0xd11f00, description=result[1])
                await message.channel.send(embed=embed)

        elif message.content == '>status':
            status = aws.get_status()
            embed = discord.Embed(
                title='Instance Status',
                color=STATUS_COLOURS[status[1]]
            )
            embed.add_field(name='Instance ID', value=status[0], inline=False)
            embed.add_field(name='Status', value=status[2].title(), inline=False)

            if status[3] != '':
                embed.add_field(name='Reason', value=status[3], inline=False)

            await message.channel.send(embed=embed)

client = MacawBot()
client.run(credentials.discord_bot_token)