import discord
from discord.ext import commands
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from utils import pages, group_list, numbered


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['h'])
    async def help(self, ctx, *cog):
        """Returns the commands for the mentioned cog/module
        alias: 'h'"""
        await ctx.message.delete()
        if not cog:
            halp = discord.Embed(
                title='Module Listing and Uncatergorized Commands',
                description='Use `$help *module*` to find out more about them!', colour=0xFFAE00)
            cogs_desc = ''
            for x in self.bot.cogs:
                if x not in ['CommandErrorHandler', 'listener', 'help', 'administration']:
                    cogs_desc += ('{} - {}'.format(x, self.bot.cogs[x].__doc__) + '\n')
            halp.add_field(name='Modules', value=cogs_desc[0:len(cogs_desc) - 1], inline=False)
            halp.set_thumbnail(url=self.bot.user.avatar_url)
            await ctx.send('', embed=halp)
        else:
            embed_help = discord.Embed(
                title=f'Commands for module {cog[0]}',
                colour=0xFFAE00
            )

            if len(cog) > 1:
                halp = discord.Embed(title='Error!', description='Only type one module after $help',
                                     color=discord.Color.red())
                await ctx.send('', embed=halp)
            else:
                for x in self.bot.cogs:
                    for y in cog:
                        if x == y:
                            for c in self.bot.get_cog(y).get_commands():
                                if not c.hidden:
                                    embed_help.add_field(
                                        name=f'{c.name}',
                                        value=f'alias: {c.aliases}'
                                    )
            await ctx.send(embed=embed_help.set_footer(
                text='Do $cmdhelp *command* to access info for said command'))

    @commands.command(aliases=['ch'])
    async def cmdhelp(self, ctx, command: str = None):
        """Returns information on the stated command
        alias: 'ch'"""
        await ctx.message.delete()
        if not command:
            await ctx.send('Do $help *module* to see commands for a module')
            return
        c = self.bot.get_command(command)
        if not c:
            await ctx.send(embed=discord.Embed(title='Command doesnt exist',
                                               description=(
                                                   'Do $help \\*module\\* to see commands for said module'),
                                               colour=0xFF0000
                                               ))
        else:
            embed_cmd = discord.Embed(
                title=f'{command}',
                description=c.help,
                colour=0xFFAE00
            )
            await ctx.send(embed=embed_cmd)


def setup(bot):
    bot.add_cog(Help(bot))
