import math

import aiosqlite
import discord
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from discord.ext import commands

from utils import group_list, numbered, pages


async def admincoords_table_create():
    async with aiosqlite.connect("coorddata") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS admincoords (
                                name text,
                                coordinates text,
                                creator integer,
                                guild_id integer
                                );""")
        await db.commit()
    print('Admincoords table created or already existed')


async def coords_table_create():
    async with aiosqlite.connect("coorddata") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS coords (
                                        user_id integer,
                                        usernick text, 
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

    @commands.command(aliases=['cs'])
    async def coordset(self, ctx, x: int, z: int, y=62):
        """Sets the coord of the user using format: (x) (z) (y defaults to 62 if not stated)
        e.g : $cs 50 50 62
        alias: 'cs'"""
        await ctx.message.delete()
        ints = [x, z, y]
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        if y > 256:
            await ctx.send('Y level cant be higher than 256 blocks :b')
            return
        else:
            await confirmation.confirm(f"Are you sure you want to set your coords as: x: {x}/ z: {z}/ y:{y}?")
            if confirmation.confirmed:
                await confirmation.update("Confirmed", color=0xFFAE00)
                str_of_coords = "/".join([str(i) for i in ints])
                async with aiosqlite.connect("coorddata") as db:
                    await db.execute(
                        """INSERT INTO coords(user_id, usernick, base_coords, guild_id) VALUES (?,?,?,?)""",
                        (ctx.author.id, ctx.author.display_name, str_of_coords, ctx.guild.id,))
                    await db.commit()
                embed_set = discord.Embed(
                    title=f'Coords set for {ctx.author.display_name} as {str_of_coords}', colour=0xFFAE00)
                await ctx.send(embed=embed_set)
            else:
                await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def coords(self, ctx, user: discord.Member = None):
        """Returns the coords of the user mentioned, if no user is mentioned, returns the author's coords
        e.g: $coords @ruffdelmo"""
        await ctx.message.delete()
        if not user:
            user = ctx.author
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute("SELECT * FROM coords WHERE guild_id=? and user_id=?",
                                  (ctx.guild.id, user.id,)) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            embed_nocrds = discord.Embed(
                title=f'No coords set for {user.display_name}', colour=0xFF0000)
            await ctx.send(embed=embed_nocrds)
        else:
            coords_list = f"{user.display_name}'s coords:\n(x)/(z)/(y)\n"
            for i in rows:
                coords_list += f"{i[2]}\n"
            embed_coords = discord.Embed(title=f"{coords_list}", colour=0xFFAE00)
            embed_coords.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed_coords)

    @commands.command()
    async def nearme(self, ctx, x: int, z: int, distance: int = 100):
        """Returns the coords and name of people near your base
        Set the coords and distance for searching as so: `$nearme 45(x) 50(z) 1000`
        If no distance is set it will default to 100"""
        async with aiosqlite.connect('coorddata') as db:
            async with db.execute("""SELECT user_id, base_coords FROM coords WHERE guild_id=? AND user_id!=?""",
                                  (ctx.guild.id, ctx.author.id)) as people_cursor:
                people_rows = await people_cursor.fetchall()
            int_people_coords = []
            for tup in people_rows:
                int_people_coords.append((tuple(tup[1].split('/'))))
            matched_coords = []
            for tup in int_people_coords:
                if await calculate_distance(x, z, int(tup[0]), int(tup[2])) <= distance:
                    matched_coords.append(f'{tup[0]}/{tup[2]}/{tup[1]}')
                else:
                    pass
            for match in matched_coords:
                async with db.execute("""SELECT user_id, base_coords FROM coords WHERE guild_id=? AND base_coords=?""",
                                      (ctx.guild.id, match)) as match_cursor:
                    matched_rows = await match_cursor.fetchall()
            embed_near = discord.Embed(title=f'People near your coords {x}/{z}:',
                                       description='Coords are in format: x, z, y')
            for match in matched_rows:
                embed_near.add_field(name=f'{self.bot.get_user(match[0]).name}\'s base',
                                     value=f'{match[1]}')
            await ctx.send(embed=embed_near)

    @commands.command()
    async def coordel(self, ctx, x: int, z: int, y=62):
        """Deletes the coords mentioned (x)(z)(y defaults to 62 if not stated)
         in the message from the database of the author
        e.g: $coordel 45 45 62"""
        await ctx.message.delete()
        ints = [x, z, y]
        str_of_coords = "/".join([str(i) for i in ints])
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0xFFAE00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=? AND base_coords=?", (
                    ctx.guild.id, ctx.author.id, str_of_coords))
                await db.commit()
            embed_delete = discord.Embed(
                title=f"{ctx.author.display_name}'s coords deleted", colour=0xFFAE00)
            await ctx.send(embed=embed_delete)
            await ctx.send('Now you live nowhere dummy :b')

        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command(aliases=['allcds'])
    async def allcoords(self, ctx):
        """Returns a list of the coords from all users
         alias: 'allcds'"""
        await ctx.message.delete()
        embed_error = discord.Embed(title='No coords set', colour=0xFF0000)
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute(
                    "SELECT user_id, base_coords FROM coords WHERE guild_id=?",
                    (ctx.guild.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    await ctx.send(embed=embed_error)
                else:
                    await (BotEmbedPaginator(ctx, pages(
                        numbered([f"{ctx.guild.get_member(r[0])}: {r[1]}" for r in rows]),
                        n=10, title=f'Coordinates for {ctx.guild}'))).run()

    @commands.command(aliases=['delucds'])
    @commands.has_permissions(administrator=True)
    async def delusercoords(self, ctx, user: discord.Member):
        """*ADMIN ONLY*
        Users with the administrator permission can delete all coords from the mentioned user
        e.g: $delucds @tigersharkpr
        alias: 'delcds'"""
        await ctx.message.delete()
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0xFFAE00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? and user_id=?", (
                    ctx.guild.id, user.id,))
                await db.commit()
            embed_delete = discord.Embed(
                title=f"{ctx.author.display_name}'s coords deleted",
                description=f'Coords deleted by {ctx.author} ', colour=0xFFAE00)
            await ctx.send(embed=embed_delete)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['sadmincrds'])
    async def setadmincoords(self, ctx, name: str, x: int, z: int, y=62):
        """*ADMIN ONLY* Sets a server coordinate by an admin, e.g: end portal coords, spawn, etc
        If the name has more than 1 word please wrap it in double quotes, e.g: "Mining District"
        e.g: '$setadmincrds "end portal" (x) (z) (y defaults to 62 if not stated)
        alias: setadmincrds"""
        await ctx.message.delete()
        ints = [x, z, y]
        str_of_coords = "/".join([str(i) for i in ints])
        async with aiosqlite.connect("coorddata") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS admincoords (
                                    name text,
                                    coordinates text,
                                    creator integer,
                                    guild_id integer
                                    );""")
            await db.execute(
                """INSERT INTO admincoords(name, coordinates, creator, guild_id) VALUES(?,?,?,?)""",
                (name, str_of_coords, ctx.author.id, ctx.guild.id))
            await db.commit()
        embed_set = discord.Embed(
            title=f'Admin coords for {name} set as {str_of_coords}',
            description=f'By {ctx.author}', colour=0xFFAE00)
        await ctx.send(embed=embed_set)

    @commands.command(aliases=['alladmincrds'])
    async def alladmincoords(self, ctx):
        """Returns all the admin coords of the current server
        alias: 'alladmincrds'"""
        await ctx.message.delete()
        embed_error = discord.Embed(title='No admin coords set', colour=0xFF0000)
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute(
                    "SELECT name, coordinates, creator FROM admincoords WHERE guild_id=?",
                    (ctx.guild.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    await ctx.send(embed=embed_error)
                else:
                    await (BotEmbedPaginator(ctx, pages(
                        numbered([f"{r[0]}: {r[1]} created by {ctx.guild.get_member(r[2])}" for r in rows]),
                        n=10, title=f'Admin coordinates for {ctx.guild}'))).run()

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['deladmincrds'])
    async def deleteadmincoords(self, ctx, name: str):
        """*ADMIN ONLY* Deletes the admin coords belonging to the name stated
        e.g : $deladmincrds "end portal"
        alias: 'deladmincrds'"""
        await ctx.message.delete()
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            async with aiosqlite.connect("coorddata") as db:
                await db.execute(
                    """DELETE FROM admincoords WHERE name=? AND guild_id=?""",
                    (name, ctx.guild.id,))
                await db.commit()
            embed_del = discord.Embed(
                title=f'Admin coords for {name} deleted',
                description=f'Deleted by {ctx.author}', colour=0xFF0000)
            await ctx.send(embed=embed_del)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)


def setup(bot):
    bot.add_cog(coordinates(bot))
