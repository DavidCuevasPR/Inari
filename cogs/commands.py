import discord
import asyncio
from discord.ext import commands
import aiosqlite
from configs.configs import reload_config, config


class C0mmands (commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def reloadconfig(self, ctx: commands.Context):
        reload_config()

    streamlink = 'https://www.twitch.tv/tigersharkpr13'

    @commands.command()
    async def phrog(self, ctx):
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

    @commands.command()
    async def marv(self, ctx):
        url = "https://i.imgur.com/wlJHI79.jpg"
        await ctx.send(
            embed=discord.Embed(title="*M A R V*").set_image(url=url))

    @commands.command()
    async def phrogbomb(self, ctx):
        url = 'https://i.imgur.com/MmoyMap.jpg'
        await ctx.send(embed=discord.Embed(title="*Le phrogge bombah*").set_image(url=url))

    @commands.command()
    async def mods(self, ctx: commands.Context):
        await ctx.send(file=discord.File(config["modfolder"]))

    @commands.command()
    async def howtomod(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(title='https://www.unitedminecrafters.com/advanced'))

    @commands.command()
    async def author(self, ctx: commands.Context):
        author = ctx.author.id
        await ctx.send(f'Hey <@{author}>')

    @commands.command()
    async def idtonick(self, ctx: commands.Context, userid: int):
        await ctx.send(await self.bot.fetch_user(f'{userid}'))


def setup(bot):
    bot.add_cog(C0mmands(bot))
