import os

import discord
from discord.utils import find
from discord.ext import commands


token = open('token', 'r').read()
bot = commands.Bot(command_prefix='$',
                   intents=discord.Intents(guilds=True,
                                           messages=True,
                                           members=True,
                                           reactions=True))
bot.remove_command('help')


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='$help'))
    print('Inari is ready B)')


@bot.event
async def on_guild_join(guild):
    general = find(lambda x: x.name == 'general', guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(embed=discord.Embed(title="Hello, I'm Inari!",
                                               description='Do `$help` to see my modules!',
                                               colour=0xFFAE00).set_thumbnail(url=bot.user.avatar_url))


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


for filename in os.listdir('cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(token)
