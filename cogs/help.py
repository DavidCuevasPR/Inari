import discord
from discord.ext import commands


class help(commands.Cog):
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
                if x not in ['CommandErrorHandler', 'listener', 'help']:
                    cogs_desc += ('{} - {}'.format(x, self.bot.cogs[x].__doc__) + '\n')
            halp.add_field(name='Cogs', value=cogs_desc[0:len(cogs_desc) - 1], inline=False)
            halp.set_thumbnail(url=self.bot.user.avatar_url)
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


def setup(bot):
    bot.add_cog(help(bot))
