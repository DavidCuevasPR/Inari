import discord
from discord.ext import commands
import asyncio
import os
from discord.ext.commands import Bot

token = open('token', 'r').read()
bot = commands.Bot(command_prefix='$')

@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'Cogs.{extension}')
for filename in os.listdir('./Cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'Cogs.{filename[:-3]}')



bot.run(token)
