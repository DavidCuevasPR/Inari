import discord
import asyncio
from discord.ext import commands
import aiosqlite
from configs.configs import reload_config, config


class misc(commands.Cog):
    """Misc commands for fun and some utilities"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, hidden=True)
    @commands.has_permissions(add_reactions=True, embed_links=True)
    async def help(self, ctx, *cog):

        """Gets all cogs and commands of mine."""
        if not cog:
            """Cog listing.  What more?"""
            halp = discord.Embed(title='Cog Listing and Uncatergorized Commands',
                                 description='Use `$help *cog*` to find out more about them!')
            cogs_desc = ''
            for x in self.bot.cogs:
                if x not in ['CommandErrorHandler', 'listener']:
                    cogs_desc += ('{} - {}'.format(x, self.bot.cogs[x].__doc__) + '\n')
            halp.add_field(name='Cogs', value=cogs_desc[0:len(cogs_desc) - 1], inline=False)
            await ctx.message.add_reaction(emoji='🦊')
            await ctx.send('', embed=halp)
        else:
            """Helps me remind you if you pass too many args."""
            if len(cog) > 1:
                halp = discord.Embed(title='Error!', description='That is way too many cogs!',
                                     color=discord.Color.red())
                await ctx.send('', embed=halp)
            else:
                """Command listing within a cog."""
                found = False
                for x in self.bot.cogs:
                    for y in cog:
                        if x == y:
                            halp = discord.Embed(title=cog[0] + ' Command Listing',
                                                 description=self.bot.cogs[cog[0]].__doc__)
                            for c in self.bot.get_cog(y).get_commands():
                                if not c.hidden:
                                    halp.add_field(name=c.name, value=c.help, inline=False)
                            found = True
                if found:
                    await ctx.send(embed=halp)
                if not found:
                    """Reminds you if that cog doesn't exist."""
                    halp = discord.Embed(title='Error!', description='How do you even use "' + cog[0] + '"?',
                                         color=discord.Color.red())
                    await ctx.send(embed=halp)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reloadconfig(self, ctx: commands.Context):
        message = ctx.message
        await message.delete(delay=1)
        reload_config()

    streamlink = 'https://www.twitch.tv/tigersharkpr13'

    @commands.command()
    async def phrog(self, ctx):
        """Sends a picture of a phrog"""
        message = ctx.message
        await message.delete(delay=1)
        url = 'https://cdn.discordapp.com/attachments/722691331339583551/722691369713270834/image0.png'
        await ctx.send(embed=discord.Embed(title="*P H R O G*").set_image(url=url))

    @commands.command()
    async def cheems(self, ctx):
        """Sends a picture of cheems"""
        message = ctx.message
        await message.delete(delay=1)
        url = 'https://i.imgur.com/HJfTbaY.png'
        await ctx.send(embed=discord.Embed(title="*C H E E M S*").set_image(url=url))

    @commands.command()
    async def marv(self, ctx):
        """Sends a picture of a beloved pet"""
        message = ctx.message
        await message.delete(delay=1)
        url = "https://i.imgur.com/wlJHI79.jpg"
        await ctx.send(
            embed=discord.Embed(title="*M A R V*").set_image(url=url))

    @commands.command()
    async def phrogbomb(self, ctx):
        """A bunch of phrogs"""
        message = ctx.message
        await message.delete(delay=1)
        url = 'https://i.imgur.com/MmoyMap.jpg'
        await ctx.send(embed=discord.Embed(title="*Le phrogge bombah*").set_image(url=url))

    @commands.command(aliases=['me'])
    async def author(self, ctx: commands.Context):
        """Returns a greeting from the bot to the author, alias: 'me'"""
        message = ctx.message
        await message.delete(delay=1)
        author = ctx.author.id
        await ctx.send(f'Hey <@{author}>')

    @commands.command(aliases=['itn'])
    async def idtoname(self, ctx: commands.Context, userid: int):
        """Returns the name of the user using their id, alias: 'itn'"""
        message = ctx.message
        await message.delete(delay=1)
        await ctx.send(await self.bot.fetch_user(f'{userid}'))


def setup(bot):
    bot.add_cog(misc(bot))
