import discord
from discord.ext import commands


class Help(commands.Cog):
    """Help commands for finding commands and knowing their uses"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['h'])
    async def help(self, ctx, command: str = None):
        """Returns the commands for the mentioned cog/module
        alias: 'h'"""
        await ctx.message.delete()
        if not command:
            halp = discord.Embed(
                title='Module Listing and Uncategorized Commands',
                description='Use `$commands(or $cmds) *module*` to see the commands of the module!',
                colour=0xFFAE00)
            cogs_desc = ''
            for x in self.bot.cogs:
                if x not in ['CommandErrorHandler', 'listener', 'Help', 'administration']:
                    cogs_desc += ('{} - {}'.format(x, self.bot.cogs[x].__doc__) + '\n')
            halp.add_field(name='Modules', value=cogs_desc[0:len(cogs_desc) - 1], inline=False)
            halp.set_thumbnail(url=self.bot.user.avatar_url)
            await ctx.send('', embed=halp)
        else:
            c = self.bot.get_command(command)
            if not c:
                await ctx.send(embed=discord.Embed(
                    title='That command does not exist',
                    description='Do `$cmds *module*` to see commands for a module',
                    colour=0xFF0000))
                return
            else:
                embed_cmd = discord.Embed(
                    title=command,
                    description=c.help,
                    colour=0xFFAE00
                )
                await ctx.send(embed=embed_cmd.set_footer(text='Do $help to see more modules'))

    @commands.command(aliases=['cmds'])
    async def commands(self, ctx, module: str = None):
        await ctx.message.delete()
        if not module:
            await ctx.send(embed=discord.Embed(
                title='Do `$commands *module*` to see commands for a module', colour=0xFFAE00))
            return
        else:
            cg: commands.Cog = self.bot.get_cog(module)
            if cg is None:
                await ctx.send(embed=discord.Embed(
                    title='Module does not exist',
                    description='Do `$help` to see a list of modules',
                    colour=0xFF0000))
                return
            else:
                embed_commands = discord.Embed(
                    title=f'Commands for module {cg.qualified_name}',
                    colour=0xFFAE00
                )
                for cmd in self.bot.get_cog(module).get_commands():
                    if not cmd.hidden:
                        embed_commands.add_field(
                            name=cmd.name,
                            value=f'alias: {cmd.aliases}'
                        )
                await ctx.send(embed=embed_commands.set_footer(
                    text='Do $help *command* to access info for said command'))


def setup(bot):
    bot.add_cog(Help(bot))
