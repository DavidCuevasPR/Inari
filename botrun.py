import discord
from discord.ext import commands
import asyncio
import os
from discord.ext.commands import Bot
import yaml

token = open('token', 'r').read()
bot = commands.Bot(command_prefix='$')


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


for filename in os.listdir('cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(token)
