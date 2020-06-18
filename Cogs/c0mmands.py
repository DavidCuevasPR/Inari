import discord
from discord.ext import commands
import asyncio
import os
from discord.ext.commands import Bot

class c0mmands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    streamlink = 'https://www.twitch.tv/tigersharkpr13'

    @commands.command()
    async def phrog(self,ctx):
        url = 'https://cdn.discordapp.com/attachments/722691331339583551/722691369713270834/image0.png'
        await ctx.send(embed=discord.Embed(title="*P H R O G*").set_image(url=url))

    @commands.command()
    async def cheems(self, ctx):
        url = 'https://i.imgur.com/HJfTbaY.png'
        await ctx.send(embed=discord.Embed(title="*C H E E M S*").set_image(url=url))

    @commands.command()
    async def stream(self, ctx):
        streamlink = 'https://www.twitch.tv/tigersharkpr13'
        await ctx.send('@everyone Stream ahora mismo en:' + streamlink)

    url = "https://i.imgur.com/wlJHI79.jpg"

    @commands.command()
    async def marv(self, ctx):
        url = "https://i.imgur.com/wlJHI79.jpg"
        await ctx.send(
            embed=discord.Embed(title="*M A R V*").set_image(url=url))

    @commands.command()
    async def phrogbomb(self, ctx):
        url = 'https://i.imgur.com/MmoyMap.jpg'
        await ctx.send(embed=discord.Embed(title="*Le phrogge bombah*").set_image(url=url))




def setup(bot):
    bot.add_cog(c0mmands(bot))

