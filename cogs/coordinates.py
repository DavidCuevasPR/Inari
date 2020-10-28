import math
from dataclasses import dataclass

import aiosqlite
import discord
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from discord.ext import commands

from utils import numbered, pages


@dataclass
class UserCoords:
    user_id: int
    name: str
    base_coords: str
    guild_id: int


@dataclass
class AdminCoords:
    name: str
    coords: str
    creator_id: int
    guild_id: int


async def admincoords_table_create():
    async with aiosqlite.connect("coorddata.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS admincoords (
                                name text,
                                coordinates text,
                                creator integer,
                                guild_id integer
                                );""")
        await db.commit()
    print('Admincoords table created or already existed')


async def coords_table_create():
    async with aiosqlite.connect("coorddata.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS coords (
                                        user_id integer,
                                        name text, 
                                        base_coords text,
                                        guild_id integer
                                        );""")
        await db.commit()
    print('Coords table created or already existed')


async def calculate_distance(x1, z1, x2, z2):
    dist = math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)
    return round(dist)


class coordinates(commands.Cog):
    """Commands to create and store coordinates for your Minecraft server"""
    def __init__(self, bot):
        self.bot = bot
        self.usercoords = []
        self.admincoords = []
        bot.loop.create_task(self.startup())

    async def startup(self):
        async with aiosqlite.connect("coorddata.db") as db:
            await coords_table_create()
            await admincoords_table_create()
            await db.commit()

            async with db.execute("""SELECT * FROM coords""") as cursor:
                usercoord_rows = await cursor.fetchall()
                if usercoord_rows:
                    for coord_tup in usercoord_rows:
                        ucoord = UserCoords(user_id=coord_tup[0], name=coord_tup[1],
                                            base_coords=coord_tup[2], guild_id=coord_tup[3])
                        self.usercoords.append(ucoord)

            async with db.execute("""SELECT * FROM admincoords""") as cursor:
                admincoord_rows = await cursor.fetchall()
                if admincoord_rows:
                    for admin_tup in admincoord_rows:
                        adm_coord = AdminCoords(name=admin_tup[0], coords=admin_tup[1],
                                                creator_id=admin_tup[2], guild_id=admin_tup[3])
                        self.admincoords.append(adm_coord)

    @commands.command(aliases=['cs'])
    async def coordset(self, ctx, x: int, z: int, y=62, name=''):
        """
        Sets the coord of the user using format and a name(base, spawner, etc)
        e.g : $coordset <x> <z> <y> <name>
        alias: 'cs'
        """
        await ctx.message.delete()
        ints = [x, z, y]
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        if y > 256:
            await ctx.send(embed=discord.Embed(title='Y level can\'t be higher than 256 blocks',
                                               colour=0xFF0000))
            return
        await confirmation.confirm(f"Are you sure you want to set your coords as:\n"
                                   f" x: {x}/ z: {z}/ y: {y}/ name: {name}?")
        if confirmation.confirmed:
            str_of_coords = "/".join([str(i) for i in ints])
            async with aiosqlite.connect("coorddata.db") as db:
                await db.execute(
                    """INSERT INTO coords(user_id, name, base_coords, guild_id) VALUES (?,?,?,?)""",
                    (ctx.author.id, name, str_of_coords, ctx.guild.id,))
                await db.commit()

            ucoord = UserCoords(user_id=ctx.author.id, name=name,
                                base_coords=str_of_coords, guild_id=ctx.guild.id)
            self.usercoords.append(ucoord)
            await confirmation.update(f"Coords set for {ctx.author.display_name}(Name: {name}) as {str_of_coords}",
                                      color=0xFFAE00)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def coords(self, ctx, user: discord.Member = None):
        """
        Returns the coords of the user mentioned, if no user is mentioned, returns the author's coords
        e.g: $coords @ruffdelmo
        """
        await ctx.message.delete()
        if not user:
            user = ctx.author
        if user.id not in [ucoords.user_id for ucoords in self.usercoords if ucoords.guild_id == ctx.guild.id]:
            embed_nocrds = discord.Embed(
                title=f'No coords set for {user.display_name}', colour=0xFF0000)
            await ctx.send(embed=embed_nocrds)
        else:
            gen = [
                ucoords.base_coords + ' ' + ucoords.name + '\n'
                for ucoords in self.usercoords if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id
            ]
            coords_list = f"{user.display_name}'s coords:\n(x)/(z)/(y)/(name)\n"
            for coords in gen:
                coords_list += coords
            embed_coords = discord.Embed(title=f"{coords_list}", colour=0xFFAE00)
            embed_coords.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed_coords)

    @commands.command()
    async def nearme(self, ctx, x: int, z: int, distance: int = 100):
        """
        Returns the coords and name of people near your base
        Set the coords and distance for searching as so:
        `$nearme 45(x) 50(z) 1000(distance)`
        If no distance is set it will default to 100
        """
        people_gen = [
            (ucoords.user_id, ucoords.base_coords)
            for ucoords in self.usercoords if ucoords.user_id != ctx.author.id and ucoords.guild_id == ctx.guild.id
        ]
        people_rows = people_gen
        int_people_coords = []
        for tup in people_rows:
            int_people_coords.append((tuple(tup[1].split('/'))))
        matched_coords = []
        for tup in int_people_coords:
            if await calculate_distance(x, z, int(tup[0]), int(tup[2])) <= distance:
                matched_coords.append(f'{tup[0]}/{tup[2]}/{tup[1]}')
            else:
                pass
        match_gen = [
            (ucoords.user_id, ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.guild_id == ctx.guild.id and ucoords.base_coords in matched_coords
        ]
        if not match_gen:
            await ctx.send(embed=discord.Embed(title='No coords found',
                                               colour=0xFF0000))
            return
        embed_near = discord.Embed(title=f'People near your coords {x}/{z}:',
                                   description='Coords are in format: x/z/y',
                                   colour=0xFFAE00)
        for match in match_gen:
            embed_near.add_field(name=f'{self.bot.get_user(match[0]).display_name}\'s base',
                                 value=f'{match[1]} /  {match[2]}')
        await ctx.send(embed=embed_near)

    @commands.command()
    async def coordel(self, ctx):
        """
        Deletes the coords that the user chooses from the multiple choice embed
        """
        await ctx.message.delete()
        author_coords = [
            (ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.user_id == ctx.author.id and ucoords.guild_id == ctx.guild.id
        ]
        multiple_choice = BotMultipleChoice(ctx, [coords[0] + ' ' + coords[1] for coords in author_coords],
                                            "Select the coordinates you wish to delete", colour=0xFFAE00)
        await multiple_choice.run()
        await multiple_choice.quit()
        if multiple_choice.choice:
            confirmation = BotConfirmation(ctx, 0xFFAE00)
            await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
            if confirmation.confirmed:
                for ucoords in self.usercoords:
                    if (ucoords.base_coords + ' ' + ucoords.name == multiple_choice.choice
                            and ucoords.guild_id == ctx.guild.id and ucoords.user_id == ctx.author.id):
                        self.usercoords.remove(ucoords)
                async with aiosqlite.connect("coorddata.db") as db:
                    await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=? AND base_coords=?", (
                        ctx.guild.id, ctx.author.id, multiple_choice.choice))
                    await db.commit()
                await confirmation.update(f"Your coords({multiple_choice.choice}), have been deleted", color=0xFFAE00)
            else:
                await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command(aliases=['allcrds'])
    async def allcoords(self, ctx):
        """
        Returns a list of the coords from all users
        alias: 'allcrds'
        """
        await ctx.message.delete()
        embed_error = discord.Embed(title='No coords set', colour=0xFF0000)
        allcoords_gen = [
            (ucoords.user_id, ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.guild_id == ctx.guild.id
        ]
        if not allcoords_gen:
            await ctx.send(embed=embed_error)
        else:
            await (BotEmbedPaginator(ctx, pages(
                numbered([f"{ctx.guild.get_member(tup[0]).display_name}: {tup[1] + ' / ' + tup[2]}"
                          for tup in allcoords_gen]),
                n=10, title=f'Coordinates for {ctx.guild.name}'))).run()

    @commands.command(aliases=['delucrds'])
    @commands.has_permissions(administrator=True)
    async def delusercoords(self, ctx, user: discord.Member):
        """
        *ADMIN ONLY*
        Users with the administrator permission can select and delete coords from the mentioned user
        e.g: $delucds @tigersharkpr
        alias: 'delucrds'
        """
        await ctx.message.delete()
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        delcoords_gen = [
            (ucoords.base_coords,)
            for ucoords in self.usercoords if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id
        ]
        if not delcoords_gen:
            await ctx.send(embed=discord.Embed(title="This user doesn't have any registered coords",
                                               colour=0xFF0000))
            return
        multiple_choice = BotMultipleChoice(ctx,
                                            [coords[0] for coords in delcoords_gen] + ['Delete all coords'],
                                            "Select the coordinates you wish to delete", colour=0xFFAE00)
        await multiple_choice.run()
        await multiple_choice.quit()
        async with aiosqlite.connect("coorddata.db") as db:
            if multiple_choice.choice == 'Delete all coords':
                await confirmation.confirm(f"Are you sure you want to delete all coords for this user?")
                if confirmation.confirmed:
                    await confirmation.update("Confirmed", color=0xFFAE00)
                    await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=?", (
                        ctx.guild.id, user.id))
                    await db.commit()
                    for ucoords in self.usercoords:
                        if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id:
                            self.usercoords.remove(ucoords)
                    embed_delete = discord.Embed(
                        title=f"All of {user.display_name}'s coords deleted",
                        colour=0xFFAE00)
                    await ctx.send(embed=embed_delete)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

            elif multiple_choice.choice:
                await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
                if confirmation.confirmed:
                    await confirmation.update("Confirmed", color=0xFFAE00)
                    await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=? AND base_coords=?", (
                        ctx.guild.id, user.id, multiple_choice.choice))
                    await db.commit()
                    for ucoords in self.usercoords:
                        if (ucoords.base_coords == multiple_choice.choice
                                and ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id):
                            self.usercoords.remove(ucoords)
                    embed_delete = discord.Embed(
                        title=f"{user.display_name}'s {multiple_choice.choice} coords deleted", colour=0xFFAE00)
                    await ctx.send(embed=embed_delete)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['setadmcrds'])
    async def setadmincoords(self, ctx, name: str, x: int, z: int, y=62):
        """
        *ADMIN ONLY* Sets a server coordinate by an admin, e.g: end portal coords, spawn, etc
        If the name has more than 1 word please wrap it in double quotes, e.g: "Mining District"
        e.g: '$setadmincrds "end portal" (x) (z) (y defaults to 62 if not stated)
        alias: setadmincrds
        """
        await ctx.message.delete()
        if y > 256:
            await ctx.send(embed=discord.Embed(title='Y level can\'t be higher than 256 blocks',
                                               colour=0xFF0000))
            return
        ints = [x, z, y]
        str_of_coords = "/".join([str(i) for i in ints])
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm(f"Are you sure you want to set the admin coords as:\n"
                                   f" {name} x: {x}/ z: {z}/ y:{y}?")
        if confirmation.confirmed:
            await confirmation.update(f'Admin coords for {name} set as\n'
                                      f'{str_of_coords} by {ctx.author.display_name}',
                                      color=0xFFAE00)
            async with aiosqlite.connect("coorddata.db") as db:
                await db.execute(
                    """INSERT INTO admincoords(name, coordinates, creator, guild_id) VALUES(?,?,?,?)""",
                    (name, str_of_coords, ctx.author.id, ctx.guild.id))
                await db.commit()
            adm_coords = AdminCoords(name=name, coords=str_of_coords,
                                     creator_id=ctx.author.id, guild_id=ctx.guild.id)
            self.admincoords.append(adm_coords)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command(aliases=['alladmincrds'])
    async def alladmincoords(self, ctx):
        """
        Returns all the admin coords of the current server
        alias: 'alladmincrds'
        """
        await ctx.message.delete()
        embed_error = discord.Embed(title='No admin coords set', colour=0xFF0000)
        alladm_gen = [
            (adm.name, adm.coords, adm.creator_id)
            for adm in self.admincoords if adm.guild_id == ctx.guild.id
        ]
        if not alladm_gen:
            await ctx.send(embed=embed_error)
        else:
            await (BotEmbedPaginator(ctx, pages(
                numbered(
                    [f"{tup[0]}: {tup[1]} | Creator: {ctx.guild.get_member(tup[2]).display_name}"
                     for tup in alladm_gen]
                ), n=10, title=f'Admin coordinates for {ctx.guild.name}\n (name)(x)(z)(y)'))).run()

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['deladmincrds'])
    async def deleteadmincoords(self, ctx):
        """
        *ADMIN ONLY* Deletes the admin coords selected from the multiple choice
        alias: 'deladmincrds'
        """
        await ctx.message.delete()
        deladmin_gen = [
            (adm.name,)
            for adm in self.admincoords if adm.guild_id == ctx.guild.id
        ]
        async with aiosqlite.connect("coorddata.db") as db:
            multiple_choice = BotMultipleChoice(ctx, [tup[0] for tup in deladmin_gen],
                                                "Select the coords you wish to delete", colour=0xFFAE00)
            await multiple_choice.run()
            await multiple_choice.quit()
            confirmation = BotConfirmation(ctx, 0xFFAE00)
            if multiple_choice.choice:
                await confirmation.confirm("Are you sure?")
                if confirmation.confirmed:
                    for adm in self.admincoords:
                        if adm.name == multiple_choice.choice and adm.guild_id == ctx.guild.id:
                            self.admincoords.remove(adm)
                    await db.execute(
                        """DELETE FROM admincoords WHERE name=? AND guild_id=?""",
                        (multiple_choice.choice, ctx.guild.id,))
                    await db.commit()
                    embed_del = discord.Embed(
                        title=f'Admin coords for {multiple_choice.choice} deleted',
                        description=f'Deleted by {ctx.author.display_name}', colour=0xFF0000)
                    await ctx.send(embed=embed_del)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)


def setup(bot):
    bot.add_cog(coordinates(bot))
