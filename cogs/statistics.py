import discord
from discord.ext import commands, tasks
from discord.utils import find
import datetime
import aiosqlite


class statistics(commands.Cog):
    """Statistics for guilds"""

    def __init__(self, bot):
        self.bot = bot

    async def guild_check(self):
        """Checks that all the guilds the bot is in are in the database,
        if not the bot inserts the guild.id into the database"""
        async with aiosqlite.connect('guildgrowth.db') as db:
            for guild in self.bot.guilds:
                async with db.execute("""SELECT guild_id FROM guildgrowth WHERE guild_id=? """,
                                      (guild.id,)) as cursor:
                    rows = await cursor.fetchall()
                    if not rows:
                        await db.execute("""INSERT INTO guildgrowth (guild_id, stats_on) VALUES (?,?)""",
                                         (guild.id, 'On',))
            await db.commit()

    async def weekday_insert(self, weekday: int):
        """Takes in a datetime.datetime.weekday and inserts the member count for the guild
        in the respective date column"""
        async with aiosqlite.connect('guildgrowth.db') as db:
            if weekday == 0:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET monday=?, sent=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), 'No', guild.id, 'On',))

            elif weekday == 1:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET tuesday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))

            elif weekday == 2:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET wednesday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))

            elif weekday == 3:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET thursday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))

            elif weekday == 4:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET friday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))

            elif weekday == 5:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET saturday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))

            elif weekday == 6:
                for guild in self.bot.guilds:
                    await db.execute(
                        """UPDATE guildgrowth SET sunday=? WHERE guild_id=? AND stats_on=?""",
                        (len(self.bot.get_guild(guild.id).members), guild.id, 'On',))
                    async with db.execute(
                            """SELECT stats_on, sent FROM guildgrowth WHERE guild_id=?""",
                            (guild.id,)) as first_cursor:
                        check = await first_cursor.fetchall()
                        if check[0][0] == 'Off':
                            pass
                        else:
                            if check[0][1] == 'Yes':
                                pass
                            else:
                                async with db.execute(
                                        """SELECT monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM 
                                            guildgrowth WHERE guild_id=?""", (guild.id,)) as cursor:
                                    raw_week_report = await cursor.fetchall()
                                    week_report = []
                                    for day in raw_week_report[0]:
                                        if not day:
                                            day = 0
                                            week_report.append(day)
                                        else:
                                            week_report.append(day)

                                embed_report = discord.Embed(
                                    title=f'Weekly growth report for {guild.name}',
                                    description='If a day with the value 0 doesnt seem right, it may be '
                                                'due to the bot not being on that day and adding 0 '
                                                'as a substitute value',
                                    colour=0xFFAE00)

                                week = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                                        4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
                                for num in range(0, 7):
                                    embed_report.add_field(name=f'{week[num]}', value=f'{week_report[num]}')

                                if int(week_report[6]) > int(
                                        week_report[0]):  # comparison between Sunday and Monday
                                    sun_minus_mon = week_report[6] - week_report[0]
                                    embed_report.set_footer(
                                        text=f'Your server has grown by {sun_minus_mon} members')

                                elif int(week_report[0]) > int(week_report[6]):
                                    mon_minus_sun = week_report[0] - week_report[6]
                                    embed_report.set_footer(
                                        text=f'Your server has grown by {mon_minus_sun} members')

                                elif int(week_report[0]) == int(week_report[6]):
                                    embed_report.set_footer(text='Your server has not grown')

                                general = find(lambda x: x.name == 'general', guild.text_channels)
                                if general and general.permissions_for(guild.me).send_messages:
                                    await general.send(embed=embed_report)
                                    await db.execute("""UPDATE guildgrowth SET sent=? WHERE guild_id=?""",
                                                     ('Yes', guild.id,))
                await db.commit()

    @tasks.loop(hours=8)
    async def weekday_check(self):
        """Checks the weekday for use in the other functions,
         runs those functions and creates the table if it doesnt exist in the database"""
        weekday = datetime.datetime.weekday(datetime.datetime.now())
        async with aiosqlite.connect('guildgrowth.db') as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS guildgrowth (
                                guild_id INTEGER,
                                monday INTEGER,
                                tuesday INTEGER,
                                wednesday INTEGER,
                                thursday INTEGER,
                                friday INTEGER,
                                saturday INTEGER,
                                sunday INTEGER,
                                stats_on TEXT
                                );""")
            await db.commit()
            await self.guild_check()
            await self.weekday_insert(weekday)

    @commands.command()
    async def statson(self, ctx):
        """Turns stats on or off for the server (Stats are turned on by default)"""
        async with aiosqlite.connect('guildgrowth.db') as db:
            async with db.execute("""SELECT stats_on FROM guildgrowth WHERE guild_id=?""",
                                  (ctx.guild.id,)) as cursor:
                stats_on = await cursor.fetchall()
                if stats_on[0] == ('On',):
                    await db.execute("""UPDATE guildgrowth SET stats_on=? WHERE guild_id=?""",
                                     ('Off', ctx.guild.id,))
                    await ctx.send(embed=discord.Embed(title='Statistics for this server are now deactivated',
                                                       colour=0xFFAE00))
                elif stats_on[0] == ('Off',):
                    await db.execute("""UPDATE guildgrowth SET stats_on=? WHERE guild_id=?""",
                                     ('On', ctx.guild.id,))
                    await ctx.send(embed=discord.Embed(title='Statistics for this server are now activated',
                                                       colour=0xFFAE00))
            await db.commit()

    @commands.command()
    async def statsnow(self, ctx):
        """Returns the weekly report up until the present day"""
        weekday = datetime.datetime.weekday(datetime.datetime.now())
        week = {0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday', 4: 'friday', 5: 'saturday', 6: 'sunday'}
        async with aiosqlite.connect('guildgrowth.db') as db:
            async with db.execute("""SELECT monday, tuesday, wednesday, thursday, friday, saturday, sunday, stats_on 
                                     FROM guildgrowth WHERE guild_id=?""", (ctx.guild.id,)) as cursor:
                raw_rows = await cursor.fetchall()
                checked_rows = []
                for members in raw_rows[0]:
                    if not raw_rows:
                        members = 0
                        checked_rows.append(members)
                    else:
                        checked_rows.append(members)

                if raw_rows[0][7] == 'Off':
                    await ctx.send(embed=discord.Embed(title='Statistics for this server are deactivated',
                                                       description='Do `$statson` to activate stats',
                                                       colour=0xFFAE00))
                else:
                    embed_report = discord.Embed(
                        title=f'Weekly growth from monday to {week[weekday]} for {ctx.guild.name}',
                        description='If a day with the value 0 doesnt seem right, it may be '
                                    'due to the bot not being on that day and adding 0 as a substitute value',
                        colour=0xFFAE00)

                    for day in range(0, weekday+1):
                        embed_report.add_field(name=f'{week[day]}', value=f'{checked_rows[day]}')

                    await ctx.send(embed=embed_report)


def setup(bot):
    bot.add_cog(statistics(bot))
